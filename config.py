CONFIG = {
    'SERVER_HOST': '127.0.0.1',
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
