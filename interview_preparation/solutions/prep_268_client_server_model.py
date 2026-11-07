"""Small specified application model, NOT a network server/transport implementation."""


class ChatModel:
    def __init__(self):
        self.connected = set()
        self.events = []
        self.seen = {}

    def connect(self, client):
        self.connected.add(client)

    def disconnect(self, client):
        self.connected.discard(client)

    def send(self, client, request_id, text):
        if client not in self.connected:
            raise ValueError("client must be authenticated and connected")
        if type(request_id) is not str or type(text) is not str or not text:
            raise ValueError("nonempty text and string request identifier required")
        key = client, request_id
        if key in self.seen:
            sequence, original = self.seen[key]
            if text != original:
                raise ValueError("request identifier reused for another payload")
            return sequence
        sequence = len(self.events) + 1
        self.events.append((sequence, client, text))
        self.seen[key] = sequence, text
        return sequence

    def resume(self, client, last_sequence):
        if client not in self.connected or type(last_sequence) is not int:
            raise ValueError("connected client and integer cursor required")
        if not 0 <= last_sequence <= len(self.events):
            raise ValueError("cursor outside retained event history")
        return [event for event in self.events if event[0] > last_sequence]
