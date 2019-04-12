import errno
import socket
import select
from common.packet_handler import CommPacketHandler
from common.packet_handler import CommHeader
from common.packet_handler import NameResponsePayload


class SocketClient:
    def __init__(self, name, port, host='127.0.0.1'):
        self.name = name
        self._packet_handler = CommPacketHandler()
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._outbound_byte_buffer = bytearray()

        print("SocketClient: connecting on {}:{}".format(host, port))
        # FIXME make this sensible
        self._socket.connect((host, port))
        print("SocketClient: connected on {}:{}".format(host, port))
        self._inout = [self._socket]

    def poll(self):
        readable, writeable, errored = select.select(list(self._inout),
                                                     list(self._inout),
                                                     list(self._inout),
                                                     0.5)

        if len(readable) > 0:
            self._packet_handler.add_bytes(self._socket.recv(4096))

        if len(writeable) > 0:
                if len(self._outbound_byte_buffer) > 0:
                    try:
                        print("sending bytes: {}".format(self._outbound_byte_buffer))
                        sent = self._socket.send(self._outbound_byte_buffer)
                        self._outbound_byte_buffer = self._outbound_byte_buffer[sent:]
                        print("Sent {} bytes".format(sent))

                    except socket.error as e:
                        if e.errno != errno.EAGAIN:
                            self._socket.close()
                            # FIXME uuhhhh
                            print("woopsie daisy")
                            raise e

                        print('Blocking with', len(self._outbound_byte_buffer), 'remaining')

        if len(errored) > 0:
            self._socket.close()
            # FIXME uuhhhh
            raise Exception("woopsie daisy")

        self.process_received_packets()

    def process_received_packets(self):
        for packet in self._packet_handler.available_packets:
            if packet["msgtype"] == "name_request":
                print("SocketClient: name request received")
                payload = NameResponsePayload(name=self.name)
                header = CommHeader(msgtype="name_reply", payload_len=len(payload.get_bytes()))

                self.send_bytes(header.get_bytes() + payload.get_bytes())

                self._packet_handler.available_packets.remove(packet)

    def send_bytes(self, bytes):
        if len(self._outbound_byte_buffer) == 0:
            self._outbound_byte_buffer = bytes
        else:
            self._outbound_byte_buffer.extend(bytes)

    def get_bytes(self):
        self._packet_handler.add_bytes(self._socket.recv(4096))

    def close(self):
        self._socket.close()
