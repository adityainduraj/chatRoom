import socket
import threading
import json
from config import CONFIG
from models import Client, Message
from utils import log_message

class ChatServer:
    def __init__(self):
        self.clients = {}  # username -> Client object
        self.socket = None

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((CONFIG['SERVER_HOST'], CONFIG['SERVER_PORT']))
        self.socket.listen(CONFIG['MAX_CONNECTIONS'])
        log_message("Server started successfully")
        print("Server running!")

        while True:
            try:
                conn, addr = self.socket.accept()
                threading.Thread(target=self.handle_client_connection,
                               args=(conn, addr)).start()
            except Exception as e:
                log_message(f"Error accepting connection: {e}", 'error')

    def handle_client_connection(self, conn, addr):
        # First message should be username
        try:
            username = conn.recv(CONFIG['BUFFER_SIZE']).decode()
            client = Client(conn, addr, username)
            self.clients[username] = client

            self.broadcast_message(
                Message('status', f'{username} joined the chat', 'Server')
            )

            self.handle_client_messages(client)
        except Exception as e:
            log_message(f"Error handling client connection: {e}", 'error')

    def handle_client_messages(self, client):
        while True:
            try:
                data = client.connection.recv(CONFIG['BUFFER_SIZE'])
                if not data:
                    break

                msg = Message.from_json(data.decode())
                if msg.type == 'command':
                    self.handle_command(msg, client)
                elif msg.type == 'dm':
                    self.handle_private_message(msg)
                else:
                    self.broadcast_message(msg, exclude=client.username)

            except Exception as e:
                log_message(f"Error handling message: {e}", 'error')
                break

        self.remove_client(client.username)

    def broadcast_message(self, message, exclude=None):
        for username, client in self.clients.items():
            if username != exclude:
                try:
                    client.connection.send(message.to_json().encode())
                except:
                    self.remove_client(username)

    def handle_command(self, message, client):
        if message.content == 'users':
            response = Message('command',
                             f"Online users: {', '.join(self.clients.keys())}",
                             'Server')
            client.connection.send(response.to_json().encode())

    def handle_private_message(self, message):
        if message.recipient in self.clients:
            self.clients[message.recipient].connection.send(
                message.to_json().encode()
            )

    def remove_client(self, username):
        if username in self.clients:
            self.clients[username].connection.close()
            del self.clients[username]
            self.broadcast_message(
                Message('status', f'{username} left the chat', 'Server')
            )

if __name__ == "__main__":
    server = ChatServer()
    server.start()
