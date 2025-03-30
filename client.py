# Used ChatGPT to help debug through fernet
import socket
import threading
import time
import redis
import hashlib
import base64
from cryptography.fernet import Fernet

# The server specifications
DISCOVERY_SERVER = ("localhost", 5001)
REDIS_SERVER = ("localhost", 6379)

def get_chat_key(user1, user2):
    names = sorted([user1, user2])
    combined = (names[0] + names[1]).encode()
    hash_digest = hashlib.sha256(combined).digest()
    key = base64.urlsafe_b64encode(hash_digest[:32])
    return key

class Client:
    def __init__(self, username, listen_port):
        self.username = username
        self.listen_port = listen_port
        self.blocked_users = set()
        self.muted_users = {}
        self.redis_client = redis.Redis(host=REDIS_SERVER[0], port=REDIS_SERVER[1], decode_responses=True)
        self.start_redis_subscription()
        self.register_with_discovery_server()
        self.keep_alive_thread = threading.Thread(target=self.keep_alive, daemon=True)
        self.keep_alive_thread.start()
        self.p2p_server_thread = threading.Thread(target=self.start_p2p_server, daemon=True)
        self.p2p_server_thread.start()
    
    def register_with_discovery_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(DISCOVERY_SERVER)
            message = f"REGISTER:{self.username}:{self.listen_port}"
            s.send(message.encode())
            response = s.recv(1024).decode()
            print(f"Discovery server response: {response}")
            s.close()
        except Exception as e:
            print(f"Error registering with discovery server: {e}")
    
    def keep_alive(self):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(DISCOVERY_SERVER)
                message = f"KEEPALIVE:{self.username}"
                s.send(message.encode())
                s.recv(1024)
                s.close()
            except Exception as e:
                print(f"Keep-alive error: {e}")
            time.sleep(10)
    
    def discover_peers(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(DISCOVERY_SERVER)
            message = f"DISCOVER:{self.username}"
            s.send(message.encode())
            data = s.recv(4096).decode()
            s.close()
            peers = {}
            if data:
                entries = data.split(";")
                for entry in entries:
                    if entry:
                        parts = entry.split(",")
                        if len(parts) == 3:
                            uname, ip, port = parts
                            peers[uname] = (ip, int(port))
            return peers
        except Exception as e:
            print(f"Error discovering peers: {e}")
            return {}
    
    def start_p2p_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("", self.listen_port))
        server.listen(5)
        print(f"P2P server listening on port {self.listen_port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_p2p_connection, args=(conn, addr), daemon=True).start()
    
    def handle_p2p_connection(self, conn, addr):
        try:
            data = conn.recv(4096)
            if data:
                text = data.decode()
                parts = text.split(":", 3)
                if len(parts) >= 4 and parts[0] == "SENDER" and parts[2] == "MESSAGE":
                    sender = parts[1]
                    encrypted_message = parts[3]
                    if sender in self.blocked_users:
                        print(f"Message from blocked user {sender} ignored.")
                    else:
                        mute_until = self.muted_users.get(sender, 0)
                        if time.time() < mute_until:
                            print(f"Message from muted user {sender} ignored.")
                        else:
                            f = Fernet(get_chat_key(self.username, sender))
                            try:
                                decrypted = f.decrypt(encrypted_message.encode()).decode()
                                print(f"[{sender}] {decrypted}")
                            except Exception as e:
                                print(f"Error decrypting message from {sender}: {e}")
            conn.close()
        except Exception as e:
            print(f"Error handling P2P connection: {e}")
    
    def send_message(self, target_username, message_text):
        if target_username in self.blocked_users:
            print(f"You have blocked {target_username}. Cannot send message.")
            return
        
        peers = self.discover_peers()
        if target_username not in peers:
            print(f"{target_username} is not currently online. Storing message in Redis queue.")
            self.store_offline_message(target_username, message_text)
            return
        
        ip, port = peers[target_username]
        f = Fernet(get_chat_key(self.username, target_username))
        encrypted_message = f.encrypt(message_text.encode()).decode()
        formatted = f"SENDER:{self.username}:MESSAGE:{encrypted_message}"
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, port))
            s.send(formatted.encode())
            s.close()
        except Exception as e:
            print(f"Error sending message to {target_username}: {e}. Storing in Redis queue.")
            self.store_offline_message(target_username, message_text)
    
    def store_offline_message(self, target_username, message_text):
        f = Fernet(get_chat_key(self.username, target_username))
        encrypted_message = f.encrypt(message_text.encode()).decode()
        payload = f"{self.username}:{encrypted_message}"
        self.redis_client.rpush(f"offline:{target_username}", payload)
    
    def check_offline_messages(self):
        key = f"offline:{self.username}"
        while True:
            message = self.redis_client.lpop(key)
            if message is None:
                break
            try:
                sender, encrypted_message = message.split(":", 1)
                f = Fernet(get_chat_key(self.username, sender))
                decrypted = f.decrypt(encrypted_message.encode()).decode()
                print(f"[Offline][{sender}] {decrypted}")
            except Exception as e:
                print(f"Error processing offline message: {e}")
    
    def start_redis_subscription(self):
        threading.Thread(target=self.redis_subscription_thread, daemon=True).start()
    
    def redis_subscription_thread(self):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe("special")
        print("Subscribed to special messages channel.")
        for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                print(f"[Special Message] {data}")
    
    def block_user(self, target_username):
        self.blocked_users.add(target_username)
        print(f"Blocked user {target_username}.")
    
    def mute_user(self, target_username, duration):
        self.muted_users[target_username] = time.time() + duration
        print(f"Muted user {target_username} for {duration} seconds.")
    
    def run(self):
        print("Client started. Type 'help' for commands.")
        while True:
            self.check_offline_messages()
            cmd = input(">> ").strip()
            if cmd == "help":
                print("Commands:")
                print("  list - list online peers")
                print("  send <username> <message> - send message to a peer")
                print("  block <username> - block a user")
                print("  mute <username> <seconds> - mute a user for given seconds")
                print("  quit - exit")
            elif cmd == "list":
                peers = self.discover_peers()
                if peers:
                    print("Online peers:")
                    for uname, (ip, port) in peers.items():
                        print(f"  {uname}: {ip}:{port}")
                else:
                    print("No peers online.")
            elif cmd.startswith("send"):
                parts = cmd.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: send <username> <message>")
                else:
                    target = parts[1]
                    message_text = parts[2]
                    self.send_message(target, message_text)
            elif cmd.startswith("block"):
                parts = cmd.split(" ", 1)
                if len(parts) < 2:
                    print("Usage: block <username>")
                else:
                    self.block_user(parts[1])
            elif cmd.startswith("mute"):
                parts = cmd.split(" ", 2)
                if len(parts) < 3:
                    print("Usage: mute <username> <seconds>")
                else:
                    try:
                        duration = int(parts[2])
                        self.mute_user(parts[1], duration)
                    except:
                        print("Invalid duration.")
            elif cmd == "quit":
                print("Exiting...")
                break
            else:
                print("Unknown command. Type 'help' for list of commands.")

def main():
    username = input("Enter your username: ").strip()
    port_input = input("Enter port to listen on (e.g., 6000): ").strip()
    try:
        listen_port = int(port_input)
    except:
        print("Invalid port number.")
        return
    client = Client(username, listen_port)
    client.run()

if __name__ == "__main__":
    main()
