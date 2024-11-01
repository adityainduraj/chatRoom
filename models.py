import json
from datetime import datetime

class Message:
    def __init__(self, type, content, sender, recipient=None):
        self.type = type
        self.content = content
        self.sender = sender
        self.recipient = recipient
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_json(self):
        """Convert message to JSON string with proper encoding"""
        data = {
            'type': self.type,
            'content': self.content,
            'sender': self.sender,
            'recipient': self.recipient,
            'timestamp': self.timestamp
        }
        return json.dumps(data)  # Remove newline addition

    @staticmethod
    def from_json(json_str):
        """Parse JSON string to Message object with proper handling"""
        try:
            json_str = json_str.strip()
            data = json.loads(json_str)
            msg = Message(
                type=data.get('type', 'chat'),
                content=data.get('content', ''),
                sender=data.get('sender', 'unknown')
            )
            msg.timestamp = data.get('timestamp', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            msg.recipient = data.get('recipient')
            return msg
        except json.JSONDecodeError as e:
            print(f"Error decoding message: {e}")
            return Message('error', 'Invalid message format', 'System')
class Client:
    def __init__(self, connection, address, username):
        self.connection = connection
        self.address = address
        self.username = username
        self.buffer = ""  # Add buffer for incomplete messages
