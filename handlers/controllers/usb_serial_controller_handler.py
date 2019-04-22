from handlers.controllers.controller_handler import ControllerHandler
from handlers.packet_handler import CommPacketHandler
import time


class UsbSerialControllerHandler(ControllerHandler):
    def __init__(self, config, serial_manager):
        self._serial_manager = serial_manager
        self.name = config.get("name")
        self._packet_handler = CommPacketHandler()

        ControllerHandler.__init__(self, config)

        self.events = list()

        self._request_timeout = 0.1
        self._request_interval = 1.0 / 30
        self._last_request = 0
        self._waiting_reply = False

        self.state_query_pkt = [ord('~'), 0xfd]

    def validate_config(self, config):
        if "port" not in config.keys():
            raise Exception("LedFixture: config contains no port")

    def is_connected(self):
        return self._serial_manager.is_connected(self.name)

    def update(self):
        if self._serial_manager.is_connected(self.name):

            if self._waiting_reply and self._last_request + self._request_timeout < time.time():
                self._waiting_reply = False

            if not self._waiting_reply:
                if self._last_request + self._request_interval < time.time():
                    self._last_request = time.time()
                    self._serial_manager.send_request(self.name, "state_request")
                    self._waiting_reply = True

            for packet in self._serial_manager.get_packets(self.name):
                if packet["msgtype"] == "state_reply":
                    self._waiting_reply = False
                    buttons = packet["button_state"]
                    sliders = packet["slider_state"]

                    for i in range(len(buttons)):
                        if i in self._buttons.keys():
                            self._buttons[i].set_state(buttons[i])

                            if buttons[i]:
                                self._add_event(self._buttons[i])

                    for i in range(len(sliders)):
                        if i in self._sliders.keys():
                            self._sliders[i].set_state(sliders[i])

                            if self._sliders[i].changed():
                                self._add_event(self._sliders[i])

                else:
                    raise Exception("UsbSerialControllerHandler: unhandled packet type ", packet["msgtype"])

            self._serial_manager.clear_packets(self.name)

        else:
            self._waiting_reply = False
