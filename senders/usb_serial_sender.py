from senders.sender import Sender
from common.usb_serial_port import UsbSerialPort


class UsbSerialSender(Sender):
    def __init__(self, config):
        Sender.__init__(self, config)
        self.validate_config(config)
        self.port = config.get("port", "")

        self._serial = UsbSerialPort(config)

    def validate_config(self, config):
        if "port" not in config.keys():
            raise Exception("LedFixture: config contains no port")

    def is_connected(self):
        return self._serial.is_connected()

    def try_connect(self):
        self._serial.try_connect()

    def send(self, line, pixels):
        if line > self.num_lines or line < 0:
            raise Exception("Sender: send called on invalid line {}".format(line))

        # if not connected, drop frame
        if self.is_connected():

            packet  = self.encapsulate(line, list(channel for pixel in pixels for channel in pixel))

            self._serial.send_bytes(packet)

    def encapsulate(self, line, payload):
        header = [ord('~'), line]
        footer = [ord('|')]

        # avoid sentinel value
        for char in payload:
            if char == header[0] or char == footer[0]:
                char += 1

        return bytearray(header + payload + footer)
