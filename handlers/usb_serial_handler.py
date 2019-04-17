import serial
from serial.tools import list_ports_posix
import time


class SerialPortInfo:
    def __init__(self):
        self.name = ""
        self.srl = None
        self.name_requested = False
        self.good = False
        self.errored = False
        self.last_send_time = 0.0


class UsbSerialHandler:
    def __init__(self):
        self.attached_ports = dict()
        self.stale_ports = list()

        self.name_query_pkt = [ord('~'), 0xfe]
        self.send_interval = 0.0005

    def update(self):
        available_ports = list(port[0] for port in list_ports_posix.comports() if port[1] == 'USB Serial')

        # close absent ports
        for port in self.attached_ports.keys():
            if port not in available_ports:
                if self.attached_ports[port].good:
                    print("Lost connection with sender {} on port {}".format(self.attached_ports[port].name, port))
                else:
                    print("Serial USB device disappeared on {}".format(port))

                if self.attached_ports[port].srl:
                    self.attached_ports[port].srl.close()

                self.stale_ports.append(port)

        for port in self.stale_ports:
            self.attached_ports.pop(port)
            self.stale_ports.clear()

        # register present ports
        for port in available_ports:
            if port not in self.attached_ports.keys():
                print("Serial USB device detected on {}".format(port))
                self.attached_ports[port] = SerialPortInfo()

        # connect and get names
        for port, portinfo in self.attached_ports.items():
            if not portinfo.srl:
                try:
                    portinfo.srl = serial.Serial(port,
                                                 parity=serial.PARITY_NONE,
                                                 stopbits=serial.STOPBITS_ONE,
                                                 bytesize=serial.EIGHTBITS,
                                                 writeTimeout=0,
                                                 timeout=0,
                                                 rtscts=False,
                                                 dsrdtr=False,
                                                 xonxoff=False)

                except:
                    portinfo.errored = True

            elif not portinfo.name_requested:
                try:
                    print("requesting name on {}".format(port))
                    # request name
                    portinfo.srl.write(self.name_query_pkt)
                    portinfo.name_requested = True

                except Exception as e:
                    print(e)
                    portinfo.errored = True

            # wait for name reply
            elif not portinfo.good and not portinfo.errored:
                while portinfo.srl.in_waiting:
                    portinfo.name += "".join(chr(x) for x in portinfo.srl.read())

                # de-encapsulate name
                if len(portinfo.name) > 2:
                    if portinfo.name[0] == "~" and portinfo.name[-1] == "|":
                        portinfo.name = portinfo.name[1:-1]
                        print("Serial device on {} identified as {}".format(port, portinfo.name))
                        portinfo.good = True

    # check for connection and handle logging
    def is_connected(self, name):
        return name in list(portinfo.name for portinfo in self.attached_ports.values() if portinfo.good)

    def send_bytes(self, name, packet):
        for port, portinfo in self.attached_ports.items():
            if portinfo.name == name:
                if not portinfo.good:
                    return

                # don't retry if interval hasn't passed
                if portinfo.last_send_time + self.send_interval > time.time():
                    return

                portinfo.last_send_time = time.time()

                if portinfo.srl.isOpen():
                    try:
                        portinfo.srl.write(packet)

                    except Exception as e:
                        print("Sender {} lost connection on port {}".format(portinfo.name, port))
                        portinfo.srl.close()
                        self.stale_ports.append(port)

    def get_bytes(self, name):
        buffer = list()

        for port, portinfo in self.attached_ports.items():
            if portinfo.name == name:
                if not portinfo.good:
                    return buffer

                if portinfo.srl.isOpen():
                    try:
                        while portinfo.srl.in_waiting:
                            buffer.append(portinfo.srl.read())

                    except Exception as e:
                        print("Sender {} lost connection on port {}".format(portinfo.name, port))
                        portinfo.srl.close()
                        self.stale_ports.append(port)

        return buffer
