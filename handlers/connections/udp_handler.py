from handlers.connections.connection_handler import ConnectionHandler
from handlers.packet_handler import CommHeader
import time
import socket
import select

class NodeInfo:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.last_seen = time.time()
        self.inbound_packet_buffer = list()
        self.last_sent = 0.0

class UdpHandler(ConnectionHandler):
    def __init__(self, port, timeout=0.001, node_timeout=5.0):
        ConnectionHandler.__init__(self)

        self.sock = socket.socket(socket.AF_INET,  # Internet
                                  socket.SOCK_DGRAM)  # UDP

        self.sock.setsockopt (socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.last_ping = 0.0
        self.ping_interval = 1.0
        self.port = port
        self.timeout = timeout
        self.node_timeout = node_timeout

        self.udp_broadcast = "192.168.1.255"

        self.ip = socket.gethostbyname(socket.gethostname())
        server_address = ("", port)

        print(f"UdpHandler binding on address {server_address}...")
        self.sock.bind(server_address)
        print(f"UdpHandler bound.")
        # print(self.sock.gethostbyname(socket.gethostname()))

        self.nodes = dict()

        self.send_interval = 1.0 / 30.0

    def poll(self):
        if self.last_ping + self.ping_interval < time.time():
            self.send_ping()
            self.last_ping = time.time()

        self.handle_incoming()
        self.prune_nodes()

    def handle_incoming(self):
        readable, writeable, errored = select.select([self.sock],
                                                     [self.sock],
                                                     [self.sock],
                                                     self.timeout)

        # only handle incoming if there is incoming to handle
        if self.sock not in readable:
            return

        incoming, addr = self.sock.recvfrom(4096)

        if len(incoming) == 0:
            return

        remote_ip = addr[0]
        remote_port = addr[1]

        if remote_ip == self.ip:
            # skip broadcast messages from ourself
            return

        hdr = CommHeader(bytes=incoming[0:CommHeader.header_len])
        hdr_dict = hdr.get_dict()
        incoming = incoming[CommHeader.header_len:]

        node_id = int.from_bytes(incoming[0:4], byteorder='big', signed=False)
        node_str = '{}'.format(f'0x{node_id:08x}')
        incoming = incoming[4:]

        if node_id in self.nodes:
            self.nodes[node_id].last_seen = time.time()

        if hdr_dict["msgtype"] == "ping_reply":
            if node_id not in self.nodes.keys() or self.nodes[node_id].address != remote_ip:
                print(f"Node {node_str} discovered at ip {remote_ip}")
                self.nodes[node_id] = NodeInfo(remote_ip, remote_port)

        else:
            return
            print(f"{remote_ip} : {self.ip}")
            print(f"received {len(incoming)} bytes: {incoming}")
            self.nodes[node_id].inbound_packet_buffer.append(incoming)

    def prune_nodes(self):
        stale_nodes = list()

        for node, node_info in self.nodes.items():
            if node_info.last_seen + self.node_timeout < time.time():
                print("Node {} timed out".format(f"0x{node:08x}"))
                stale_nodes.append(node)

        for node in stale_nodes:
            del self.nodes[node]

    def send_ping(self):
        request_bytes = CommHeader(msgtype="ping_request").get_bytes()

        # UDP requests expect a node ID
        for _ in range(4):
            request_bytes.append(0x00)

        self.sock.sendto(request_bytes, ('255.255.255.255', self.port))

    def is_connected(self, node_id):
        return node_id in self.nodes.keys()

    def get_packets(self, node_id):
        # just drop bytes for unknown clients for now
        if node_id in self.nodes.keys():
            return self.nodes[node_id].inbound_packet_buffer

        return list()

    def clear_packets(self, node_id):
        # just drop bytes for unknown clients for now
        if node_id in self.nodes.keys():
            self.nodes[node_id].inbound_packet_buffer.clear()

    def send_request(self, node_id, request):
        # just drop request for unknown clients for now
        if node_id in self.nodes.keys():
            request_bytes = CommHeader(msgtype=request).get_bytes()
            request_bytes.extend(node_id.to_bytes(4, byteorder="big"))

            self.sock.sendto(request_bytes, (self.nodes[node_id].address, self.nodes[node_id].port))

    def send_bytes(self, node_id, bytes):
        # just drop bytes for unknown clients for now
        if node_id in self.nodes.keys():
            if self.nodes[node_id].last_sent + self.send_interval < time.time():
                self.nodes[node_id].last_sent = time.time()
                self.sock.sendto(bytes, (self.nodes[node_id].address, self.nodes[node_id].port))

    def handle_received_packets(self):
        pass
