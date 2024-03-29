import numpy as np
import time
import os
from overlays.overlay import Overlay
from common.dynamic_loader import get_module_classes
from common.utils import camel_to_snake


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
        classes = get_module_classes(overlays_dir)
        for name, obj in classes.items():
            if issubclass(obj, Overlay) and obj != Overlay:
                snake_case_name = camel_to_snake(name)
                self.overlays[snake_case_name] = obj

    def get_overlays(self):
        return self.overlays

    def update(self):
        self.active_overlays = list(overlay for overlay in self.active_overlays if time.time() - overlay.start_time < self.min_time or overlay.get_max_contribution_per_led() > self.epsilon)

    def receive_command(self, command):
        if command["type"] == "overlay":
            if command['name'] in self.overlays.keys():
                self.active_overlays.append(OverlayInfo(self.overlays[command['name']](command['args'])))
            else:
                raise Exception("OverlayHandler: unknown overlay {}".format(command["name"]))

        else:
            raise Exception("OverlayHandler: unknown command type {}".format(command["type"]))

    def calculate_overlaid_colours(self, leds, colours, fixture_name):
        overlaid_colours = colours

        for overlay in self.active_overlays:
            overlaid_colours = overlay.get_overlaid_colours(overlaid_colours, leds, fixture_name)

        return overlaid_colours
