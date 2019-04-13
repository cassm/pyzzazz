from controllers.controller_handler import ControllerHandler
from common.usb_serial_port import UsbSerialPort
from common.packet_handler import CommPacketHandler


class UsbSerialControllerHandler(ControllerHandler):
    def __init__(self, config):
        self.validate_config(config)
        self.port = config.get("port", "")

        ControllerHandler.__init__(self, config)

        self._serial = UsbSerialPort(config)
        self._packet_handler = CommPacketHandler()

        self._waiting_for_packet = False
        self.events = list()

    def validate_config(self, config):
        if "port" not in config.keys():
            raise Exception("LedFixture: config contains no port")

    def is_connected(self):
        return self._serial.is_connected()

    def try_connect(self):
        self._serial.try_connect()

    def update(self):
        # don't accept mangled frames if we can help it
        if not self.is_connected():
            self._packet_handler.clear()

        self._packet_handler.add_bytes(self._serial.get_bytes())

    def get_events(self):
        for packet in self._packet_handler.available_packets:
            for index, state in enumerate(packet.button_state):
                if index in self._buttons and state != self._buttons[index].last_state:
                    self._buttons[index].set_state(state)
                    self._add_event(self._buttons[index], state)

            for index, state in enumerate(packet.slider_state):
                if index in self._sliders and state != self._sliders[index].last_state:
                    self._sliders[index].set_state(state)
                    self._add_event(self._buttons[index], state)
