# Handling multiple clients for server

class Port_handler:
    def __init__(self, client):
        self.client_address = client[0]
        self.client_port = client[1]
