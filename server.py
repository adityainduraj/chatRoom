# server.py
import socket
import threading
import json
from config import CONFIG, get_local_ip, find_available_port
from models import Client, Message
from utils import log_message, print_colored
import signal
import sys
import openai

# Set your OpenAI API key here
openai.api_key = 'YOUR_OPENAI_API_KEY'

class ChatServer:
    def __init__(self):
        self.clients = {}  # username -> Client object
        self.socket = None
        self.server_ip = get_local_ip()
        self.running = True
        self.port = CONFIG['SERVER_PORT']

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Handle shutdown signals gracefully"""
        print_colored("\nReceived shutdown signal. Closing server...", "yellow")
        self.shutdown()
        sys.exit(0)

    def start(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.settimeout(CONFIG['SOCKET_TIMEOUT'])

            # Try to bind to default port, if fails, find an available port
            try:
                self.socket.bind(('0.0.0.0', self.port))
            except OSError:
                print_colored(f"Default port {self.port} is in use, searching for available port...", "yellow")
                available_port = find_available_port()
                if available_port:
                    self.port = available_port
                    try:
                        self.socket.bind(('0.0.0.0', self.port))
                        print_colored(f"Successfully bound to port {self.port}", "green")
                    except OSError as e:
                        print_colored(f"Error binding to port {self.port}: {e}", "red")
                        return
                else:
                    print_colored(f"No available ports found in range {CONFIG['PORT_RANGE_START']}-{CONFIG['PORT_RANGE_END']}", "red")
                    return

            self.socket.listen(CONFIG['MAX_CONNECTIONS'])

            print_colored("\n=== Chat Server Started ===", "green")
            print_colored(f"Server IP: {self.server_ip}", "blue")
            print_colored(f"Port: {self.port}", "blue")
            print_colored("Share these details with clients to connect.", "yellow")
            print_colored("Press Ctrl+C to shutdown server.", "yellow")
            print_colored("Waiting for connections...\n", "yellow")

            log_message("Server started successfully")

            while self.running:
                try:
                    conn, addr = self.socket.accept()
                    threading.Thread(target=self.handle_client_connection,
                                   args=(conn, addr)).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    log_message(f"Error accepting connection: {e}", 'error')
                    if not self.running:
                        break

        except Exception as e:
            print_colored(f"Server error: {e}", "red")
            log_message(f"Server error: {e}", 'error')
        finally:
            self.shutdown()

    def handle_client_connection(self, conn, addr):
        try:
            # Set timeout for client connections
            conn.settimeout(CONFIG['CLIENT_TIMEOUT'])

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
        while self.running:
            try:
                data = client.connection.recv(CONFIG['BUFFER_SIZE'])
                if not data:
                    break

                try:
                    msg = Message.from_json(data.decode())
                    log_message(f"Message from {client.username}: {msg.content}")

                    if msg.type == 'command':
                        self.handle_command(msg, client)
                    elif msg.type == 'dm':
                        self.handle_private_message(msg)
                    else:
                        self.broadcast_message(msg, exclude=client.username)
                        # Send message to chatbot and broadcast response
                        chatbot_response = self.get_chatbot_response(msg.content)
                        if chatbot_response:
                            self.broadcast_message(
                                Message('chat', chatbot_response, 'Chatbot')
                            )
                except Exception as e:
                    log_message(f"Error processing message: {e}", 'error')

            except Exception as e:
                log_message(f"Error handling message from {client.username}: {e}", 'error')
                break

        self.remove_client(client.username)

    def get_chatbot_response(self, user_message):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=user_message,
                max_tokens=150
            )
            return response.choices[0].text.strip()
        except Exception as e:
            log_message(f"Error getting chatbot response: {e}", 'error')
            return None

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
        """Shutdown the server and clean up connections"""
        self.running = False
        print_colored("\nShutting down server...", "yellow")

        # Notify all clients about server shutdown
        shutdown_msg = Message('status', 'Server is shutting down...', 'Server')
        self.broadcast_message(shutdown_msg)

        # Close all client connections
        for client in list(self.clients.values()):
            try:
                client.connection.close()
            except:
                pass
        self.clients.clear()

        # Close server socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        print_colored("Server shutdown complete.", "green")
        log_message("Server shutdown complete")

if __name__ == "__main__":
    server = ChatServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.shutdown()
