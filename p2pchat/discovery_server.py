# Used ChatGPT to help resolve port errors
import socket
import threading
import time

users = {}
lock = threading.Lock()
KEEPALIVE_TIMEOUT = 30

def client_handler(conn, addr):
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break
            print(f"Received from {addr}: {data}")
            parts = data.strip().split(":")
            command = parts[0]
            if command == "REGISTER":
                if len(parts) >= 3:
                    username = parts[1]
                    port = int(parts[2])
                    with lock:
                        users[username] = {"ip": addr[0], "port": port, "last_seen": time.time()}
                    conn.send("REGISTERED".encode())
            elif command == "KEEPALIVE":
                if len(parts) >= 2:
                    username = parts[1]
                    with lock:
                        if username in users:
                            users[username]["last_seen"] = time.time()
                    conn.send("ALIVE".encode())
            elif command == "DISCOVER":
                if len(parts) >= 2:
                    username = parts[1]
                    with lock:
                        result = []
                        for user, info in users.items():
                            if user != username and time.time() - info["last_seen"] < KEEPALIVE_TIMEOUT:
                                result.append(f"{user},{info['ip']},{info['port']}")
                    response = ";".join(result)
                    conn.send(response.encode())
            else:
                conn.send("UNKNOWN COMMAND".encode())
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def cleanup_users():
    while True:
        time.sleep(10)
        with lock:
            to_delete = [user for user, info in users.items() 
                         if time.time() - info["last_seen"] > KEEPALIVE_TIMEOUT]
            for user in to_delete:
                print(f"Removing user {user} due to timeout")
                del users[user]

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", 5001))
    server_socket.listen(5)
    print("Discovery Server listening on port 5001")
    t = threading.Thread(target=cleanup_users, daemon=True)
    t.start()

    while True:
        conn, addr = server_socket.accept()
        threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
