# config.py
import socket

CONFIG = {
    'SERVER_PORT': 12000,
    'PORT_RANGE_START': 12000,
    'PORT_RANGE_END': 12100,    # Will try ports 12000-12100 if default is busy
    'MAX_CONNECTIONS': 10,
    'BUFFER_SIZE': 2048,
    'SOCKET_TIMEOUT': 1.0,    # Server socket timeout in seconds
    'CLIENT_TIMEOUT': 60.0,   # Client socket timeout in seconds
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
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def is_port_available(port):
    """Check if a port is available"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('0.0.0.0', port))
        available = True
    except OSError:
        available = False
    finally:
        sock.close()
    return available

def find_available_port():
    """Find an available port in the configured range"""
    for port in range(CONFIG['PORT_RANGE_START'], CONFIG['PORT_RANGE_END'] + 1):
        if is_port_available(port):
            return port
    return None
