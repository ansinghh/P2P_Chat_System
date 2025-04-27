# P2P Chat System

A decentralized peer-to-peer chat system written in Python using sockets and Redis. This project demonstrates how clients can directly message one another, with offline message handling, Redis-backed synchronization, user controls (block/mute), and a centralized discovery server to bootstrap connections. The system is Dockerized for easy setup and includes unit testing and CI integration using GitHub Actions.

## Features

- Peer-to-peer messaging using Python sockets
- Central discovery server for IP/port lookup
- Asynchronous message handling with threads
- Redis for storing offline messages and broadcasting system-wide updates
- End-to-end encrypted chat using Fernet
- Block and mute controls for users
- Keep-alive mechanism to track online status
- Docker-based deployment using Docker Compose
- Unit testing with pytest and GitHub Actions CI integration

## Requirements

- Docker and Docker Compose (recommended for running the system)
- Python 3.8 or higher (if running manually without Docker)
- pip packages (if running manually):
  - redis
  - cryptography
  - pytest
  - pytest-cov

## Setup (Recommended: Docker)

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/P2P_Chat_System.git
cd P2P_Chat_System
```
2. Build the Docker images
```bash
docker-compose build
```
3. Start the system
```bash
docker-compose up
```
This will start:

- Redis server on port 6379

- Discovery server on port 5001

- One interactive client container

4. To run additional clients (in separate terminal windows)
```bash

docker-compose run client
```
When prompted:

- Enter a unique username (e.g., Bob)

- Enter a port to listen on (e.g., 6000)

Manual Setup (If Not Using Docker)
1. Install Dependencies
```bash
pip install .
pip install -r requirements-dev.txt
```
2. Start Redis server
If using macOS with Homebrew:

```bash
brew install redis
brew services start redis
```
Or manually:
```bash
redis-server
```
3. Start the discovery server
```bash
python -m p2pchat.discovery_server
```
4. Start the clients (in separate terminal windows)
```bash
python -m p2pchat.client
```
When prompted:
- Enter a unique username (e.g., Bob)
- Enter a port to listen on (e.g., 6000)

Usage
After the client starts, you’ll see:
Client started. Type 'help' for commands.

Commands:
help: Show list of commands

list: List online users

send <username> <message>: Send message to a peer

block <username>: Block a user

mute <username> <seconds>: Mute a user temporarily

quit: Exit the client

If the target user is offline, the message is stored in Redis and delivered when they come online.

How It Works
Each client registers with a centralized discovery server by sending its username and listening port.

Clients send periodic keep-alive packets so the server knows who is online.

Clients can request a list of online peers and initiate direct socket communication.

Messages are encrypted using Fernet with a shared key derived from both usernames.

Redis is used to store messages temporarily when users are offline.

A Redis Pub/Sub channel is used to broadcast "special messages" to all connected clients.

Testing
1. Install testing dependencies
```bash
pip install -r requirements-dev.txt
```
2. Run unit tests with coverage
```bash
pytest --cov=p2pchat
```
Continuous Integration (CI)
This project uses GitHub Actions for continuous integration, running unit tests automatically on every push and pull request. The Redis service is also available during CI runs for accurate testing.

The CI pipeline includes:

Pytest-based unit testing

Coverage reporting

Check the "Actions" tab on GitHub for the build and test status.

Project Files
p2pchat/: Main package containing client and discovery server modules

tests/: Unit tests

docker-compose.yml: Docker Compose configuration

Dockerfile: Docker image definition for client/server

pyproject.toml: Python packaging configuration

requirements-dev.txt: Development and testing dependencies

dump.rdb: Redis database file (auto-generated)
