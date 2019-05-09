from operator import add
from overlays.flash import Flash
from overlays.star_drive import StarDrive
from overlays.ripple import Ripple
import numpy as np
import time


class OverlayInfo:
    # FIXME add keyword?
    def __init__(self, overlay):
        self.overlay = overlay
        self.max_contribution = 0.0
        self.start_time = time.time()

    def get_overlaid_colours(self, colours, leds):
        overlaid_colours = self.overlay.get_overlaid_colours(colours, leds, time.time() - self.start_time)

        total_contribution = np.sum(np.abs((overlaid_colours - colours).flatten()))

        self.max_contribution = max(total_contribution, self.max_contribution)

        return overlaid_colours

    def get_max_contribution(self):
        max_contribution = self.max_contribution
        self.max_contribution = 0.0
        return max_contribution


class OverlayHandler:
    def __init__(self):
        self.epsilon = 10
        self.min_time = 2
        self.active_overlays = list()

    def update(self):
        self.active_overlays = list(overlay for overlay in self.active_overlays if time.time() - overlay.start_time < self.min_time or overlay.get_max_contribution() > self.epsilon)

    def receive_command(self, command):
        if command["type"] == "overlay":
            if command["name"] == "flash":
                self.active_overlays.append(OverlayInfo(Flash(command["args"])))

            elif command["name"] == "star_drive":
                self.active_overlays.append(OverlayInfo(StarDrive(command["args"])))

            elif command["name"] == "ripple":
                self.active_overlays.append(OverlayInfo(Ripple(command["args"])))

            else:
                raise Exception("OverlayHandler: unknown overlay {}".format(command["name"]))

        else:
            raise Exception("OverlayHandler: unknown command type {}".format(command["type"]))

    def calculate_overlaid_colours(self, leds, colours):
        overlaid_colours = colours

        for overlay in self.active_overlays:
            overlaid_colours = overlay.get_overlaid_colours(overlaid_colours, leds)

        return overlaid_colours
