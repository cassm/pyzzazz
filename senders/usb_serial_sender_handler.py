from senders.sender_handler import SenderHandler


class UsbSerialSenderHandler(SenderHandler):
    def __init__(self, config, serial_handler):
        SenderHandler.__init__(self, config)
        self.validate_config(config)
        self.name = config.get("name", "")
        self._serial_handler = serial_handler

        self._last_send = [0.0 for _ in range(self.num_lines)]
        self._send_interval = 1.0 / 30.0 / self.num_lines # 30 frames per second for n lines

    def validate_config(self, config):
        if "name" not in config.keys():
            raise Exception("LedFixture: config contains no name")

    def is_connected(self):
        return self._serial_handler.is_connected(self.name)

    def send(self, line, byte_values):
        if line > self.num_lines - 1 or line < 0:
            raise Exception("Sender: send called on invalid line {}".format(line))

        # if not connected, drop frame
        if self.is_connected():
            while len(byte_values) % 3:
                byte_values.append(0)

            # packet = [ord('~'), line, len(byte_values)/3]
            sentinels = [ord('~'), ord('|')]

            packet = [ord('~'), line]

            for value in byte_values:
                if value in sentinels:
                    value += 1
                packet.append(value)

            packet.append(ord('|'))

            self._serial_handler.send_bytes(self.name, packet)

    def encapsulate(self, line, payload):
        header = [ord('~'), line]
        footer = [ord('|')]

        # avoid sentinel value
        for char in payload:
            if char == header[0] or char == footer[0]:
                char += 1

        return bytearray(header + payload + footer)
