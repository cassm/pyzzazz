from handlers.connections.connection_handler import ConnectionHandler
from handlers.connections.connection_handler import ClientHandler
from handlers.connections.connection_handler import ClientState
import socket
import select
import errno


class SocketServer(ConnectionHandler):
    def __init__(self, port, host='', timeout=0.001):
        ConnectionHandler.__init__(self)

        self._timeout = timeout
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.settimeout(self._timeout)
        self._server_socket.bind((host, port))
        self._server_socket.listen()

        print("SocketServer: listening on {}:{}".format(host, port))

        self.send_buffer = bytearray()

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
                    self._client_dict[s].send_request("name_request")
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

                        else:
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
