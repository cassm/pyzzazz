import serial
import time
from sender import Sender


class UsbSerialSender(Sender):
    def __init__(self, config):
        Sender.__init__(self, config)

        self.validate_config(config)

        self.connected = False
        self.serial = serial.Serial()

        self.last_connection_time = time.time()
        self.connection_retry_interval = 1.0  # seconds
        self.previously_connected = False

        self.last_send_time = time.time()
        self.send_interval = 0.005  # seconds

    def validate_config(self, config):
        return

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
                                        baudrate=57600,
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

    def send(self, line, pixels):
        if line > self.num_lines or line < 0:
            raise Exception("Sender: send called on invalid line {}".format(line))

        # don't retry if interval hasn't passed
        if time.time() - self.last_send_time < self.send_interval:
            return

        self.last_send_time = time.time()

        # if not connected, drop frame
        if self.is_connected():

            payload = list(channel for pixel in pixels for channel in pixel)

            try:
                self.serial.write(self.encapsulate(line, payload))

            except Exception as e:
                print (e)
                # if something's wrong, drop the frame and hope it fixes itself
                pass

    def encapsulate(self, line, payload):
        header = [ord('~'), line]
        footer = [ord('|')]

        # avoid sentinel value
        for char in payload:
            if char == 126:
                char += 1

        return bytearray(header + payload + footer)

    def receive(self):
        buffer = b""

        bytes_received = 1

        while bytes_received > 0:
            char = self.serial.read()
            bytes_received = len(char)
            buffer += char

        if len(buffer) > 0:
            print(str(buffer))
