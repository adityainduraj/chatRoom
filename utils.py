# utils.py
import logging
from datetime import datetime
from config import CONFIG
from colorama import Fore, Style, init

init()

# Setup logging
logging.basicConfig(
    filename=CONFIG['LOG_FILE'],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def format_message(msg):
    """Format message with timestamp and color based on message type"""
    color = {
        'chat': Fore.WHITE,
        'status': Fore.YELLOW,
        'command': Fore.BLUE,
        'dm': Fore.GREEN
    }.get(msg.type, Fore.WHITE)

    return f"{color}[{msg.timestamp}] {msg.sender}: {msg.content}{Style.RESET_ALL}"

def print_colored(message, color):
    """Print colored message"""
    colors = {
        'red': Fore.RED,
        'green': Fore.GREEN,
        'blue': Fore.BLUE,
        'yellow': Fore.YELLOW,
        'white': Fore.WHITE
    }
    print(f"{colors.get(color, Fore.WHITE)}{message}{Style.RESET_ALL}")

def log_message(message, level='info'):
    """Log message to file"""
    getattr(logging, level)(message)
