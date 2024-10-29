# server.py
import socket
import threading
import json
from config import CONFIG, get_local_ip
from models import Client, Message
from utils import log_message, print_colored

class ChatServer:
    def __init__(self):
        self.clients = {}  # username -> Client object
        self.socket = None
        self.server_ip = get_local_ip()

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', CONFIG['SERVER_PORT']))
        self.socket.listen(CONFIG['MAX_CONNECTIONS'])

        print_colored("\n=== Chat Server Started ===", "green")
        print_colored(f"Server IP: {self.server_ip}", "blue")
        print_colored(f"Port: {CONFIG['SERVER_PORT']}", "blue")
        print_colored("Share these details with clients to connect.", "yellow")
        print_colored("Waiting for connections...\n", "yellow")

        log_message("Server started successfully")

        while True:
            try:
                conn, addr = self.socket.accept()
                threading.Thread(target=self.handle_client_connection,
                               args=(conn, addr)).start()
            except Exception as e:
                log_message(f"Error accepting connection: {e}", 'error')

    def handle_client_connection(self, conn, addr):
        try:
            username = conn.recv(CONFIG['BUFFER_SIZE']).decode()

            # Check if username already exists
            if username in self.clients:
                error_msg = Message('status', 'Username already taken. Please try again.', 'Server')
                conn.send(error_msg.to_json().encode())
                conn.close()
                return

            client = Client(conn, addr, username)
            self.clients[username] = client

            print_colored(f"New connection from {addr} - Username: {username}", "green")
            log_message(f"Client connected: {username} from {addr}")

            # Send welcome message to new client
            welcome_msg = Message('status', f'Welcome to the chat, {username}!', 'Server')
            client.connection.send(welcome_msg.to_json().encode())

            # Broadcast join message to other clients
            self.broadcast_message(
                Message('status', f'{username} joined the chat', 'Server')
            )

            self.handle_client_messages(client)

        except Exception as e:
            log_message(f"Error handling client connection: {e}", 'error')
            if conn:
                conn.close()

    def handle_client_messages(self, client):
        while True:
            try:
                data = client.connection.recv(CONFIG['BUFFER_SIZE'])
                if not data:
                    break

                msg = Message.from_json(data.decode())
                log_message(f"Message from {client.username}: {msg.content}")

                if msg.type == 'command':
                    self.handle_command(msg, client)
                elif msg.type == 'dm':
                    self.handle_private_message(msg)
                else:
                    self.broadcast_message(msg, exclude=client.username)

            except Exception as e:
                log_message(f"Error handling message from {client.username}: {e}", 'error')
                break

        self.remove_client(client.username)

    def broadcast_message(self, message, exclude=None):
        disconnected_clients = []

        for username, client in self.clients.items():
            if username != exclude:
                try:
                    client.connection.send(message.to_json().encode())
                except:
                    disconnected_clients.append(username)

        # Remove disconnected clients
        for username in disconnected_clients:
            self.remove_client(username)

    def handle_command(self, message, client):
        if message.content == 'users':
            response = Message('command',
                             f"Online users: {', '.join(self.clients.keys())}",
                             'Server')
            try:
                client.connection.send(response.to_json().encode())
            except:
                self.remove_client(client.username)

    def handle_private_message(self, message):
        if message.recipient in self.clients:
            try:
                self.clients[message.recipient].connection.send(
                    message.to_json().encode()
                )
            except:
                self.remove_client(message.recipient)

            # Send confirmation to sender
            try:
                confirm_msg = Message('status',
                                    f"Message sent to {message.recipient}",
                                    'Server')
                self.clients[message.sender].connection.send(
                    confirm_msg.to_json().encode()
                )
            except:
                self.remove_client(message.sender)
        else:
            # Notify sender that recipient is not found
            try:
                error_msg = Message('status',
                                  f"User {message.recipient} not found",
                                  'Server')
                self.clients[message.sender].connection.send(
                    error_msg.to_json().encode()
                )
            except:
                self.remove_client(message.sender)

    def remove_client(self, username):
        if username in self.clients:
            print_colored(f"Client disconnected: {username}", "yellow")
            log_message(f"Client disconnected: {username}")

            self.clients[username].connection.close()
            del self.clients[username]

            self.broadcast_message(
                Message('status', f'{username} left the chat', 'Server')
            )

    def shutdown(self):
        print_colored("\nShutting down server...", "yellow")
        for client in self.clients.values():
            client.connection.close()
        if self.socket:
            self.socket.close()
        print_colored("Server shutdown complete.", "green")

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.shutdown()
