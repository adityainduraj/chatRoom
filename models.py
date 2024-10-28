import json
from datetime import datetime

class Message:
    def __init__(self, type, content, sender, recipient=None):
        self.type = type  # 'chat', 'status', 'command', 'dm'
        self.content = content
        self.sender = sender
        self.recipient = recipient
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_str):
        data = json.loads(json_str)
        msg = Message(data['type'], data['content'], data['sender'])
        msg.timestamp = data['timestamp']
        msg.recipient = data.get('recipient')
        return msg

class Client:
    def __init__(self, connection, address, username):
        self.connection = connection
        self.address = address
        self.username = username
