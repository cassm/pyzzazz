import numpy as np
import time
import re
import os
from inspect import isclass
from pkgutil import iter_modules
from importlib import import_module
from overlays.overlay import Overlay

class OverlayInfo:
    # FIXME add keyword?
    def __init__(self, overlay):
        self.overlay = overlay
        self.max_contribution_per_led = 0.0
        self.start_time = time.time()

    def get_overlaid_colours(self, colours, leds, fixture_name):
        overlaid_colours = self.overlay.get_overlaid_colours(colours, leds, time.time() - self.start_time, fixture_name)

        total_contribution = np.sum(np.abs((overlaid_colours - colours).flatten()))

        self.max_contribution_per_led = max(total_contribution / len(leds), self.max_contribution_per_led)

        return overlaid_colours

    def get_max_contribution_per_led(self):
        max_contribution_per_led = self.max_contribution_per_led
        self.max_contribution_per_led = 0.0
        return max_contribution_per_led


class OverlayHandler:
    def __init__(self):
        self.epsilon = 10
        self.min_time = 5
        self.active_overlays = list()
        self.overlays = {}

        cwd = os.path.dirname(__file__)
        overlays_dir = os.path.join(cwd, '..', 'overlays')

        # find all subclasses of Overlay and store them by name
        for (_, module_name, _) in iter_modules([str(overlays_dir)]):
            module = import_module(f"overlays.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isclass(attr) and issubclass(attr, Overlay) and attr != Overlay:
                    # convert camelcase class name to snakecase identifier
                    snake_case_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', attr_name)
                    snake_case_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case_name)
                    snake_case_name = snake_case_name.lower()
                    self.overlays[snake_case_name] = attr

    def get_overlays(self):
        return self.overlays

    def update(self):
        self.active_overlays = list(overlay for overlay in self.active_overlays if time.time() - overlay.start_time < self.min_time or overlay.get_max_contribution_per_led() > self.epsilon)

    def receive_command(self, command):
        if command["type"] == "overlay":
            if command['name'] in self.overlays.keys():
                self.active_overlays.append(OverlayInfo(self.overlays[command['name'](command['args'])]))
            else:
                raise Exception("OverlayHandler: unknown overlay {}".format(command["name"]))

        else:
            raise Exception("OverlayHandler: unknown command type {}".format(command["type"]))

    def calculate_overlaid_colours(self, leds, colours, fixture_name):
        overlaid_colours = colours

        for overlay in self.active_overlays:
            overlaid_colours = overlay.get_overlaid_colours(overlaid_colours, leds, fixture_name)

        return overlaid_colours
