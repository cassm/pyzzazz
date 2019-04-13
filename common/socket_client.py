import errno
import socket
import select
import time
from copy import deepcopy
from common.packet_handler import CommPacketHandler
from common.packet_handler import CommHeader
from common.packet_handler import NameReplyPayload


class SocketClient:
    def __init__(self, name, port, host='127.0.0.1', timeout=0.05):
        self.name = name
        self._packet_handler = CommPacketHandler()
        self._socket = socket.socket()
        self._timeout = timeout
        self._outbound_byte_buffer = bytearray()
        self._connected = False
        self._inout = []
        self._address = (host, port)

        self._last_connection_attempt = 0
        self._connection_attempt_interval = 5

    def is_connected(self):
        return self._connected

    def try_connect(self):
        if self._connected:
            return

        if self._last_connection_attempt + self._connection_attempt_interval < time.time():
            self._last_connection_attempt = time.time()
            print("Trying to connect...")

            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(self._timeout)
                self._socket.connect(self._address)
                print("SocketClient: connected on {}".format(self._address))

                self._connected = True
                self._inout.append(self._socket)

            except socket.error:
                pass

    def poll(self):
        # check if we're awake
        # if self.is_connected():
        #     try:
        #         self._packet_handler.add_bytes(self._socket.recv(4096))
        #
        #     except socket.error as e:
        #         print ("ERROR {}".format(e))
        #         if e.args[0] in [errno.EBADF, errno.ENOTCONN]:
        #             Socket is CLOSED
                    # self._socket.close()
                    # self._inout.clear()
                    # self._connected = False
                    # print("Lost connection on {}".format(self._address))
        #
        if not self._connected:
            self.try_connect()

        readable, writeable, errored = select.select(list(self._inout),
                                                     list(self._inout),
                                                     list(self._inout),
                                                     self._timeout)

        if len(readable) > 0:
            try:
                self._packet_handler.add_bytes(self._socket.recv(4096))

            except socket.error as e:
                if e.errno != errno.EAGAIN:
                    self._socket.close()
                    self._inout.clear()
                    self._connected = False
                    print("Lost connection on {}".format(self._address))

            except Exception as e:
                self._socket.close()
                self._inout.clear()
                self._connected = False
                print("Lost connection on {}".format(self._address))

        if len(writeable) > 0:
                if len(self._outbound_byte_buffer) > 0:
                    try:
                        sent = self._socket.send(self._outbound_byte_buffer)
                        self._outbound_byte_buffer = self._outbound_byte_buffer[sent:]

                    except socket.error as e:
                        if e.errno != errno.EAGAIN:
                            self._socket.close()
                            self._inout.clear()
                            self._connected = False
                            print("Lost connection on {}".format(self._address))

                        print('Blocking with', len(self._outbound_byte_buffer), 'remaining')

                    except Exception as e:
                        self._socket.close()
                        self._inout.clear()
                        self._connected = False
                        print("Lost connection on {}".format(self._address))

        if len(errored) > 0:
            self._socket.close()
            self._inout.clear()
            self._connected = False
            print("Lost connection on {}".format(self._address))

        self.process_received_packets()

    def process_received_packets(self):
        for packet in self._packet_handler.available_packets:
            if packet["msgtype"] == "name_request":
                print("SocketClient: name request received")
                payload = NameReplyPayload(name=self.name)
                header = CommHeader(msgtype="name_reply", payload_len=len(payload.get_bytes()))

                self.send_bytes(header.get_bytes() + payload.get_bytes())

                self._packet_handler.available_packets.remove(packet)

    def send_bytes(self, bytes):
        if len(self._outbound_byte_buffer) == 0:
            self._outbound_byte_buffer = bytes
        else:
            self._outbound_byte_buffer.extend(bytes)

    def get_packets(self):
        packets = deepcopy(self._packet_handler.available_packets)
        self._packet_handler.available_packets.clear()
        return packets

    def close(self):
        self._socket.close()
