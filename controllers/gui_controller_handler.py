from controllers.controller_handler import ControllerHandler
import time


class GuiControllerHandler(ControllerHandler):
    def __init__(self, config, socket_server):
        self.validate_config(config)

        ControllerHandler.__init__(self, config)

        self.name = config.get("name")
        self._socket_server = socket_server
        self._request_timeout = 0.5
        self._last_request = 0
        self._waiting_reply = False
        self._connected = False

    def is_connected(self):
        return self._socket_server.is_connected(self.name)

    def update(self):
        if self._socket_server.is_connected(self.name):
            self._connected = True

            if self._waiting_reply and self._last_request + self._request_timeout < time.time():
                self._waiting_reply = False

            if not self._waiting_reply:
                self._socket_server.send_request(self.name, "state_request")
                self._waiting_reply = True

            for packet in self._socket_server.get_packets(self.name):
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
                    raise Exception("GuiControllerHandler: unhandled packet type")

        else:
            self._connected = False
            self._waiting_reply = False
