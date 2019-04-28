from handlers.connections.connection_handler import ClientHandler
from handlers.connections.connection_handler import ClientState
from handlers.connections.connection_handler import ConnectionHandler
import serial
import time
from sys import platform
import os


class SerialClientHandler(ClientHandler):
    def __init__(self, port):
        ClientHandler.__init__(self, port)
        self.srl = None


class UsbSerialHandler(ConnectionHandler):
    def __init__(self):
        ConnectionHandler.__init__(self)

        self.stale_ports = list()
        self.last_dev_poll = 0.0
        self.port_poll_interval = 1.0

    def update(self):
        if self.last_dev_poll + self.port_poll_interval < time.time():
            self.last_dev_poll = time.time()

            # available_ports = list(port[0] for port in list_ports_posix.comports() if port[1] == 'USB Serial')
            port_keyword = "ttyACM"

            if platform == "darwin":
                port_keyword = "tty.usbmodem"

            available_ports = list(os.path.join("/dev/", dev) for dev in os.listdir("/dev/") if str(dev).find(port_keyword) != -1)

            # close absent ports
            for port in self._client_dict.keys():
                if port not in available_ports:
                    if self._client_dict[port].state == ClientState.INITIALISED:
                        print("Lost connection with sender {} on port {}".format(self._client_dict[port].name, port))
                    else:
                        print("Serial USB device disappeared on {}".format(port))

                    if self._client_dict[port].srl:
                        self._client_dict[port].srl.close()

                    self.stale_ports.append(port)

            for port in self.stale_ports:
                self._client_dict.pop(port)
                self.stale_ports.clear()

            # register present ports
            for port in available_ports:
                if port not in self._client_dict.keys():
                    print("Serial USB device detected on {}".format(port))
                    self._client_dict[port] = SerialClientHandler(port)

        # connect and get names
        for port, client_handler in self._client_dict.items():
            if not client_handler.srl:
                try:
                    client_handler.srl = serial.Serial(port,
                                                       parity=serial.PARITY_NONE,
                                                       stopbits=serial.STOPBITS_ONE,
                                                       bytesize=serial.EIGHTBITS,
                                                       writeTimeout=0,
                                                       timeout=0,
                                                       rtscts=False,
                                                       dsrdtr=False,
                                                       xonxoff=False)

                except:
                    client_handler.errored = True

            elif client_handler.state == ClientState.NEW:
                try:
                    print("sending name request to client at {}".format(port))
                    client_handler.send_request("name_request")
                    client_handler.state = ClientState.AWAITING_NAME

                except Exception as e:
                    print(e)
                    client_handler.state = ClientState.ERRORED

        # Read data from ports and put into packet handlers
        for port, client_handler in self._client_dict.items():
            if client_handler.srl.isOpen():
                if len(client_handler.outbound_byte_buffer) > 0:
                    try:
                        client_handler.srl.write(client_handler.outbound_byte_buffer)
                        client_handler.outbound_byte_buffer = bytearray()

                    except Exception as e:
                        print(e)
                        print("Sender {} lost connection on port {}".format(client_handler.name, port))
                        client_handler.srl.close()
                        self.stale_ports.append(port)

                try:
                    while client_handler.srl.in_waiting:
                        new_bytes = client_handler.srl.read()
                        client_handler.packet_handler.add_bytes(new_bytes)

                        for packet in client_handler.packet_handler.available_packets:
                            client_handler.inbound_packet_buffer.append(packet)

                        client_handler.packet_handler.available_packets.clear()

                except Exception as e:
                    print(e)
                    print("Sender {} lost connection on port {}".format(client_handler.name, port))
                    client_handler.srl.close()
                    self.stale_ports.append(port)

        self.handle_received_packets()
