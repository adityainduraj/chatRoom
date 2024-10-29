# client.py
import socket
import threading
import json
import time
from config import CONFIG, COMMANDS
from models import Message
from utils import format_message, print_colored
import sys
from colorama import init

init()

class ChatClient:
    def __init__(self):
        self.socket = None
        self.username = None
        self.running = True
        self.server_ip = None

    def get_connection_details(self):
        while True:
            print_colored("\n=== Chat Client Connection Setup ===", "blue")
            print_colored("1. Connect to server on this computer", "yellow")
            print_colored("2. Connect to server on another computer", "yellow")
            print_colored("3. Exit", "red")

            choice = input("\nEnter your choice (1-3): ").strip()

            if choice == "1":
                self.server_ip = "127.0.0.1"
                break
            elif choice == "2":
                while True:
                    server_ip = input("\nEnter server IP address: ").strip()
                    if self.validate_ip(server_ip):
                        self.server_ip = server_ip
                        break
                    print_colored("Invalid IP address format. Please try again.", "red")
                break
            elif choice == "3":
                sys.exit(0)
            else:
                print_colored("Invalid choice. Please try again.", "red")

    def validate_ip(self, ip):
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False

    def connect(self):
        self.get_connection_details()

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            print_colored("\nAttempting to connect to server...", "yellow")
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    self.socket.connect((self.server_ip, CONFIG['SERVER_PORT']))
                    break
                except ConnectionRefusedError:
                    retry_count += 1
                    print_colored(f"Connection attempt {retry_count}/{max_retries} failed. Retrying...", "red")
                    if retry_count < max_retries:
                        time.sleep(2)

            if retry_count == max_retries:
                raise Exception("Could not connect to server after multiple attempts")

            print_colored("\nConnected to server successfully!", "green")

            while True:
                self.username = input("\nEnter your username: ").strip()
                if self.username and ' ' not in self.username:
                    break
                print_colored("Invalid username. Username cannot be empty or contain spaces.", "red")

            self.socket.send(self.username.encode())

            # Wait for initial server response
            response = self.socket.recv(CONFIG['BUFFER_SIZE'])
            initial_msg = Message.from_json(response.decode())

            if initial_msg.type == 'status' and 'already taken' in initial_msg.content:
                print_colored(initial_msg.content, "red")
                self.disconnect()
                return

            print_colored("\n=== Welcome to the Chat Room! ===", "green")
            print_colored("Type /help for available commands", "blue")
            print_colored("Type your message and press Enter to send", "blue")
            print_colored("Type /quit to exit\n", "blue")

            # Start receiver thread
            threading.Thread(target=self.receive_messages).start()
            # Start sender thread
            self.send_messages()

        except Exception as e:
            print_colored(f"\nError connecting to server: {e}", "red")
            print_colored(f"Make sure the server is running at {self.server_ip}:{CONFIG['SERVER_PORT']}", "yellow")
            self.disconnect()

    def receive_messages(self):
        while self.running:
            try:
                data = self.socket.recv(CONFIG['BUFFER_SIZE'])
                if not data:
                    break

                msg = Message.from_json(data.decode())
                print('\r' + format_message(msg))

                # Reprint the input prompt
                if hasattr(self, 'current_input'):
                    print(f"\r> {self.current_input}", end='')

            except Exception as e:
                if self.running:
                    print_colored(f"\nError receiving message: {e}", "red")
                    self.disconnect()
                break

    def send_messages(self):
        while self.running:
            try:
                self.current_input = input("> ")
                message = self.current_input

                if not message:
                    continue

                if message.startswith('/'):
                    self.handle_command(message[1:])
                else:
                    msg = Message('chat', message, self.username)
                    self.socket.send(msg.to_json().encode())

            except Exception as e:
                if self.running:
                    print_colored(f"\nError sending message: {e}", "red")
                    self.disconnect()
                break

    def handle_command(self, command):
        if command == 'quit':
            print_colored("\nDisconnecting from chat...", "yellow")
            self.disconnect()
            return

        if command == 'help':
            print_colored("\nAvailable commands:", "blue")
            for cmd, desc in COMMANDS.items():
                print_colored(f"/{cmd}: {desc}", "yellow")
            return

        if command.startswith('dm '):
            try:
                _, recipient, *content = command.split()
                if content:
                    msg = Message('dm', ' '.join(content), self.username, recipient)
                    self.socket.send(msg.to_json().encode())
                else:
                    print_colored("Error: Message content is required for DM", "red")
            except ValueError:
                print_colored("Error: Invalid DM format. Use: /dm username message", "red")
            return

        msg = Message('command', command, self.username)
        self.socket.send(msg.to_json().encode())

    def disconnect(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        print_colored("\nDisconnected from server.", "yellow")
        sys.exit(0)

if __name__ == "__main__":
    try:
        client = ChatClient()
        client.connect()
    except KeyboardInterrupt:
        client.disconnect()
