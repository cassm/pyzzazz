from copy import deepcopy
import ast


class Control:
    def __init__(self, name, id, target_regex, command, default):
        self.name = name
        self.id = id
        self.target_regex = target_regex
        self.command = command
        self.default = default
        self.state = 0
        self.last_state = 0

    def set_state(self, state):
        self.last_state = self.state
        self.state = state

    def changed(self):
        return self.state != self.last_state


class Event:
    def __init__(self, target_regex, command, value):
        self.target_regex = target_regex
        self.command = command
        self.value = value


class ControllerHandler():
    def __init__(self, config):
        self.validate_config(config)
        self.name = config.get("name", "")
        self._buttons = dict()
        self._sliders = dict()
        self._events = list()

        for button in config.get("buttons", ""):
            self._buttons[button["id"]] = Control(name=button["name"],
                                                  id=button["id"],
                                                  target_regex=button["target_regex"],
                                                  command=ast.literal_eval(button["command"]),
                                                  default=button.get("default", 0))

        for slider in config.get("sliders", ""):
            self._sliders[slider["id"]] = Control(name=slider["name"],
                                                  id=slider["id"],
                                                  target_regex=slider["target_regex"],
                                                  command=ast.literal_eval(slider["command"]),
                                                  default=slider.get("default", 50.0) / 100.0)

    def validate_config(self, config):
        if "name" not in config.keys():
            raise Exception("LedFixture: config contains no name")

    def is_connected(self):
        pass

    def try_connect(self):
        pass

    def update(self):
        pass

    def _add_event(self, control):
        self._events.append(Event(target_regex=control.target_regex, command=control.command, value=control.state))

    def get_events(self):
        return self._events

    def clear_events(self):
        self._events.clear()

    def get_controls(self):
        return list(self._buttons.values()) + list(self._sliders.values())

