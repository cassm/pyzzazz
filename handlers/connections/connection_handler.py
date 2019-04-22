from handlers.packet_handler import CommPacketHandler
from handlers.packet_handler import CommHeader
from enum import Enum


class ClientState(Enum):
    NEW = 0,
    AWAITING_NAME = 1,
    INITIALISED = 2
    ERRORED = 3


class ClientHandler:
    def __init__(self, address):
        self.address = address
        self.state = ClientState.NEW
        self.name = None
        self.packet_handler = CommPacketHandler()
        self.outbound_byte_buffer = bytearray()
        self.inbound_packet_buffer = list()

    def send_request(self, request_name):
        bytes = CommHeader(msgtype=request_name).get_bytes()
        self.send_bytes(bytes)

    def send_bytes(self, bytes):
        if len(self.outbound_byte_buffer) == 0:
            self.outbound_byte_buffer = bytes
        else:
            self.outbound_byte_buffer.extend(bytes)


class ConnectionHandler:
    def __init__(self):
        self._client_dict = dict()

    def is_connected(self, client_name):
        for client in self._client_dict.values():
            if client.name == client_name and client.state == ClientState.INITIALISED:
                return True

        return False

    def get_packets(self, client_name):
        # just drop bytes for unknown clients for now
        for client in self._client_dict.values():
            if client.name == client_name:
                return client.inbound_packet_buffer

        return list()

    def clear_packets(self, client_name):
        # just drop bytes for unknown clients for now
        for client in self._client_dict.values():
            if client.name == client_name:
                client.inbound_packet_buffer.clear()
                break

    def send_request(self, client_name, request):
        # just drop request for unknown clients for now
        for client in self._client_dict.values():
            if client.name == client_name:
                client.send_bytes(CommHeader(msgtype=request).get_bytes())

    def send_bytes(self, client_name, bytes):
        # just drop bytes for unknown clients for now
        for client in self._client_dict.values():
            if client.name == client_name:
                client.send_bytes(bytes)

    def handle_received_packets(self):
        for client in self._client_dict.values():
            for packet in client.inbound_packet_buffer:
                if packet["msgtype"] == "name_reply":
                    if client.state == ClientState.AWAITING_NAME:
                        client.name = packet["name"]
                        print("Client at {} identified as {}".format(client.address, client.name))
                        client.state = ClientState.INITIALISED

                    else:
                        if packet["name"] == client.name:
                            print("Multiple name replies received from client {} at {}".format(client.name, client.address))
                        else:
                            print("Multiple conflicting name replies received from client {}. Old name = {} new name = {}".format(client.address, client.name, packet["name"]))

                    client.inbound_packet_buffer.remove(packet)

    # handle client available packets
