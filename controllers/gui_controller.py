from tkinter import *
from common.socket_client import SocketClient
from common.packet_handler import CommHeader
from common.packet_handler import StateReplyPayload
from controllers.controller_handler import Control


class GuiControllerWindow:
    def __init__(self, name, buttons, sliders):
        self._name = name
        self._bg_colour = '#181819'
        self._window = Tk()
        self._window.title(name)
        self._window.configure(background=self._bg_colour)
        self._buttons = dict()
        self._sliders = dict()

        for butt in buttons:
            self._buttons[butt["id"]] = Control(butt["name"], butt["id"], butt["target_keyword"], butt["command"], butt.get("default, 0"))

            new_button = Button(self._window, highlightbackground=self._bg_colour, text=butt["name"],
                                command=lambda n=butt["id"]: self.button_pressed(n))

            new_button.pack({'fill': 'x', 'expand': 1, 'padx': 5, 'pady': 3})

        for slider in sliders:
            self._sliders[slider["id"]] = Control(slider["name"], slider["id"], slider["target_keyword"], slider["command"], slider["default"])
            slider_label = Label(self._window, text=slider["name"], fg="#FFFFFF", bg=self._bg_colour)
            slider_label.pack({'fill': 'x', 'expand': 1, 'padx': 5, 'pady': 3})

            new_slider = Scale(self._window, from_=0, to=100, fg='#FFFFFF', bg=self._bg_colour, orient="horizontal",
                               command=lambda value, id=slider["id"]: self.slider_moved(value, id))

            new_slider.set(slider.get("default", 50))

            new_slider.pack({'fill': 'x', 'expand': 1, 'padx': 5, 'pady': 3})

    def start(self):
        self._window.call('wm', 'attributes', '.', '-topmost', '1')
        self._window.mainloop()

    def set_after(self, interval, func):
        self._window.after(interval, func=func)

    def button_pressed(self, id):
        self._buttons[id].set_state(1)
        print("button: {}".format(id))

    def slider_moved(self, value, id):
        self._sliders[id].set_state(int(value))

    def get_button_state(self):
        button_state = list()

        # buttons may be non contiguous. default is 0
        for i in range(max(self._buttons.keys())+1):
            try:
                button_state.append(self._buttons[i].state)
            except KeyError:
                button_state.append(0)

        return button_state

        # sliders may be non contiguous. default is 0
    def get_slider_state(self):
        slider_state = list()
        for i in range(len(self._sliders.keys())):
            try:
                slider_val = int(self._sliders[i].state / 100.0 * 1024)
                slider_state.append(slider_val)
            except KeyError:
                slider_state.append(0)

        return slider_state

    def clear_button_state(self):
        for button in self._buttons.values():
            button.set_state(0)


class GuiController:
    def __init__(self, config, host):
        self.socket = SocketClient(name=config.get("name"), port=config.get("port"), host=host)
        self.window = GuiControllerWindow(config.get("name"), config.get("buttons"), config.get("sliders"))
        self.window.set_after(5, self.poll)

        self.last_update = 0.0
        self.update_interval = 5.0

    def poll(self):
        # if self.last_update + self.update_interval < time.time():
        #     print("sending update")
        #     self.last_update = time.time()
        #     self.send_state_response()

        self.socket.poll()

        for packet in self.socket.get_packets():
            if packet["msgtype"] == "state_request":
                self.send_state_reply()

        self.window.set_after(5, self.poll)

    def send_state_reply(self):
        button_state = self.window.get_button_state()
        slider_state = self.window.get_slider_state()
        self.window.clear_button_state()

        payload = StateReplyPayload(button_state=button_state, slider_state=slider_state).get_bytes()
        header = CommHeader(msgtype="state_reply", payload_len=len(payload)).get_bytes()

        self.socket.send_bytes(header + payload)

    def run(self):
        self.window.start()

