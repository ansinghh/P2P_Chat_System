# P2P Chat System

A decentralized peer-to-peer chat system written in Python using sockets and Redis. This project demonstrates how clients can directly message one another, with offline message handling, Redis-backed synchronization, user controls (block/mute), and a centralized discovery server to bootstrap connections.

## Features

- Peer-to-peer messaging using Python sockets
- Central discovery server for IP/port lookup
- Asynchronous message handling with threads
- Redis for storing offline messages and broadcasting system-wide updates
- End-to-end encrypted chat using Fernet
- Block and mute controls for users
- Keep-alive mechanism to track online status

## Requirements

- Python 3.8 or higher
- Redis (running locally)
- pip packages:
  - redis
  - cryptography
 
 ## Setup

### 1. Install Dependencies
### 2. Start Redis server If using macOS with Homebrew: brew install redis brew services start redis Or manually: redis-server
### 3. Clone the repository git clone https://github.com/<your-username>/P2P_Chat_System.git and cd P2P_Chat_System
### 4. Start the discovery server using "python3 discovery_server.py"
### 5. Start the clients (in separate terminal windows) using "python3 client.py"
  When prompted:
  
        - Enter a unique username (e.g., Bob)

        - Enter a port to listen on (e.g., 6000)

## Usage

After the client starts, you’ll see: Client started. Type 'help' for commands.

Commands:

help: Show list of commands

list: List online users

send <username> <message>: Send message to a peer

block <username>: Block a user

mute <username> <seconds>: Mute a user temporarily

quit: Exit the client

If the target user is offline, the message is stored in Redis and delivered when they come online.

## How It Works

- Each client registers with a centralized discovery server by sending its username and listening port.

- Clients send periodic keep-alive packets so the server knows who is online.

- Clients can request a list of online peers and initiate direct socket communication.

- Messages are encrypted using Fernet with a shared key derived from both usernames.

- Redis is used to store messages temporarily when users are offline.

- A Redis Pub/Sub channel is used to broadcast "special messages" to all connected clients.

## Project Files

- client.py: Main P2P chat client

- discovery_server.py: Central server for user registration and discovery

- dump.rdb: Redis database file (auto-generated)
