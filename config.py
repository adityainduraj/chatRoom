# config.py
import socket

CONFIG = {
    'SERVER_PORT': 12000,
    'MAX_CONNECTIONS': 10,
    'BUFFER_SIZE': 2048,
    'TIMEOUT': 60,
    'LOG_FILE': 'chat.log'
}

# Command prefix
CMD_PREFIX = '/'

# Available commands
COMMANDS = {
    'help': 'Show available commands',
    'users': 'List all connected users',
    'dm': 'Send private message (/dm username message)',
    'quit': 'Exit the chat'
}

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        # Create a temporary socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"
