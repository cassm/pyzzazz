from handlers.senders.sender_handler import SenderHandler
from handlers.packet_handler import CommHeader
import socket


class UdpSenderHandler(SenderHandler):
    def __init__(self, config, udp_handler):
        SenderHandler.__init__(self, config)

        self.udp_handler = udp_handler

    def is_connected(self):
        return True

    def try_connect(self):
        pass

    def send(self, node_id, byte_values):
        byte_values = list(byte_values)

        packet = CommHeader(payload_len=len(byte_values), msgtype="frame_update").get_bytes()
        packet.extend(node_id.to_bytes(4, byteorder="big"))
        packet.extend(byte_values)

        self.udp_handler.send_bytes(node_id, packet)
