import socket
import threading
import json
from config import CONFIG, COMMANDS
from models import Message
from utils import format_message
import sys
from colorama import init

init()  # Initialize colorama

class ChatClient:
    def __init__(self):
        self.socket = None
        self.username = None
        self.running = True

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((CONFIG['SERVER_HOST'], CONFIG['SERVER_PORT']))
            self.socket.settimeout(CONFIG['TIMEOUT'])

            self.username = input("Enter your username: ")
            self.socket.send(self.username.encode())

            print("Connected to chat!")
            print("Type /help for available commands")

            # Start receiver thread
            threading.Thread(target=self.receive_messages).start()
            # Start sender thread
            self.send_messages()

        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.disconnect()

    def receive_messages(self):
        while self.running:
            try:
                data = self.socket.recv(CONFIG['BUFFER_SIZE'])
                if not data:
                    break

                msg = Message.from_json(data.decode())
                print(format_message(msg))

            except Exception as e:
                print(f"Error receiving message: {e}")
                self.disconnect()
                break

    def send_messages(self):
        while self.running:
            try:
                message = input()
                if not message:
                    continue

                if message.startswith('/'):
                    self.handle_command(message[1:])
                else:
                    msg = Message('chat', message, self.username)
                    self.socket.send(msg.to_json().encode())

            except Exception as e:
                print(f"Error sending message: {e}")
                self.disconnect()
                break

    def handle_command(self, command):
        if command == 'quit':
            self.disconnect()
            return

        if command == 'help':
            print("\nAvailable commands:")
            for cmd, desc in COMMANDS.items():
                print(f"/{cmd}: {desc}")
            return

        if command.startswith('dm '):
            _, recipient, *content = command.split()
            if content:
                msg = Message('dm', ' '.join(content), self.username, recipient)
                self.socket.send(msg.to_json().encode())
            return

        msg = Message('command', command, self.username)
        self.socket.send(msg.to_json().encode())

    def disconnect(self):
        self.running = False
        if self.socket:
            self.socket.close()
        sys.exit(0)

if __name__ == "__main__":
    client = ChatClient()
    client.connect()
