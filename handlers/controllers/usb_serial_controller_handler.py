from handlers.controllers.controller_handler import ControllerHandler
from handlers.packet_handler import CommPacketHandler


class UsbSerialControllerHandler(ControllerHandler):
    def __init__(self, config, serial_manager):
        self._serial_manager = serial_manager
        self.name = config.get("name")
        self._packet_handler = CommPacketHandler()

        ControllerHandler.__init__(self, config)

        self.events = list()

    def validate_config(self, config):
        if "port" not in config.keys():
            raise Exception("LedFixture: config contains no port")

    def is_connected(self):
        return self._serial_manager.is_connected(self.name)

    def update(self):
        # don't accept mangled frames if we can help it
        if not self.is_connected():
            self._packet_handler.clear()

        self._packet_handler.add_bytes(self._serial_manager.get_bytes(self.name))

    def get_events(self):
        for packet in self._packet_handler.available_packets:
            for index, state in enumerate(packet.button_state):
                if index in self._buttons and state != self._buttons[index].last_state:
                    self._buttons[index].set_state(state)
                    self._add_event(self._buttons[index])

            for index, state in enumerate(packet.slider_state):
                if index in self._sliders and state != self._sliders[index].last_state:
                    self._sliders[index].set_state(state)
                    self._add_event(self._buttons[index])
