import socket
import select
import errno
from copy import deepcopy
from common.packet_handler import CommPacketHandler
from common.packet_handler import CommHeader
from enum import Enum

class ClientState(Enum):
    NEW = 0,
    AWAITING_NAME = 1,
    INITIALISED = 3


class ClientHandler:
    def __init__(self, address):
        self.address = address
        self.state = ClientState.NEW
        self.name = None
        self.packet_handler = CommPacketHandler()
        self.outbound_byte_buffer = bytearray()
        self.inbound_packet_buffer = list()

    def send_bytes(self, bytes):
        if len(self.outbound_byte_buffer) == 0:
            self.outbound_byte_buffer = bytes
        else:
            self.outbound_byte_buffer.extend(bytes)


class SocketServer:
    def __init__(self, port, host='', timeout=0.01):
        self._timeout = timeout
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.settimeout(self._timeout)
        self._server_socket.bind((host, port))
        self._server_socket.listen()

        print("SocketServer: listening on {}:{}".format(host, port))

        self.send_buffer = bytearray()
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

    def poll(self):
        readable, writeable, errored = select.select(list(self._client_dict.keys()) + [self._server_socket],
                                                     list(self._client_dict.keys()),
                                                     list(self._client_dict.keys()),
                                                     self._timeout)

        for s in readable:
            if s is self._server_socket:
                client_socket, address = self._server_socket.accept()
                self._client_dict[client_socket] = ClientHandler(address)
                print("Connection from {}".format(address))

            else:
                if s in self._client_dict.keys():
                    try:
                        new_bytes = bytearray(s.recv(4096))
                        self._client_dict[s].packet_handler.add_bytes(new_bytes)

                        for packet in self._client_dict[s].packet_handler.available_packets:
                            self._client_dict[s].inbound_packet_buffer.append(packet)

                        self._client_dict[s].packet_handler.available_packets.clear()

                    except socket.error as e:
                        if e.errno != errno.EAGAIN:
                            print("Lost connection with client {}".format(self._client_dict[s].name))
                            s.close()
                            self._client_dict.pop(s)

                    except Exception as e:
                        print("Lost connection with client {}".format(self._client_dict[s].name))
                        s.close()
                        self._client_dict.pop(s)

                else:
                    print("ignoring bytes read from unknown client {}".format(s))

        for s in writeable:
            if s in self._client_dict.keys():
                # don't do anything else until we have a name
                if self._client_dict[s].state == ClientState.NEW:
                    print("sending name request to client at {}".format(self._client_dict[s].address))
                    self._client_dict[s].send_bytes(CommHeader(msgtype="name_request").get_bytes())
                    self._client_dict[s].state = ClientState.AWAITING_NAME

                if len(self._client_dict[s].outbound_byte_buffer) > 0:
                    try:
                        sent = s.send(self._client_dict[s].outbound_byte_buffer)
                        self._client_dict[s].outbound_byte_buffer = self._client_dict[s].outbound_byte_buffer[sent:]

                    except socket.error as e:
                        if e.errno != errno.EAGAIN:
                            print("Lost connection with client {}".format(self._client_dict[s].name))
                            s.close()
                            self._client_dict.pop(s)

                        print('Blocking with', len(self._client_dict[s].outbound_byte_buffer), 'remaining')

                    except Exception as e:
                        print("Lost connection with client {}".format(self._client_dict[s].name))
                        s.close()
                        self._client_dict.pop(s)

            else:
                print("ignoring bytes read from unknown client {}".format(s))

        for s in errored:
            if s in self._client_dict.keys():
                print("closing errored client {} on address {}".format(self._client_dict[s].name, self._client_dict[s].address))
                self._client_dict.pop(s)
                s.close()
            else:
                # ignore unknown errored clients. Is this even possible?
                pass

        self.handle_received_packets()

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
