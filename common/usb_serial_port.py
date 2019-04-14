import serial
import time


class UsbSerialPort:
    def __init__(self, config):
        self.validate_config(config)

        self.port = config.get("port")
        self.name = config.get("name"+"_serial")

        self.connected = False
        self.serial = serial.Serial()

        self.last_connection_time = time.time()
        self.connection_retry_interval = 1.0  # seconds
        self.previously_connected = False

        self.last_send_time = time.time()
        self.send_interval = 0.0005  # seconds

    def validate_config(self, config):
        if "name" not in config.keys():
            raise Exception("UsbSerialPort: config contains no name")

        if "port" not in config.keys():
            raise Exception("UsbSerialPort: config contains no port")

    # check for connection and handle logging
    def is_connected(self):
        if self.previously_connected:
            if self.serial.isOpen():
                return True
            else:
                print("Sender {} lost connection on port {}".format(self.name, self.port))
                self.previously_connected = False
                return False
        else:
            if not self.serial.isOpen():
                return False
            else:
                print("Sender {} connected on port {}".format(self.name, self.port))
                self.previously_connected = True
                return True

    def try_connect(self):
        # don't retry if interval hasn't passed
        if time.time() - self.last_connection_time < self.connection_retry_interval:
            return

        self.last_connection_time = time.time()

        try:
            self.serial = serial.Serial(self.port,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        writeTimeout=0,
                                        timeout=0,
                                        rtscts=False,
                                        dsrdtr=False,
                                        xonxoff=False)

        except serial.SerialException:
            # Assume we can keep trying
            pass

    def send_bytes(self, packet):
        # don't retry if interval hasn't passed
        if time.time() - self.last_send_time < self.send_interval:
            return

        self.last_send_time = time.time()

        # if not connected, drop frame
        if self.is_connected():
            try:
                self.serial.write(packet)

            except Exception as e:
                print(e)
                # if something's wrong, drop the frame and hope it fixes itself
                pass

    def get_bytes(self):
        buffer = list()

        bytes_received = 1

        # if not connected, drop frame
        if self.is_connected():
            try:
                while bytes_received > 0:
                    char = self.serial.read()
                    bytes_received = len(char)
                    buffer.append(char)
            except Exception as e:
                print(e)
                # if something's wrong, drop the frame and hope it fixes itself
                pass

        return buffer
