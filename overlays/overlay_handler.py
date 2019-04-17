from operator import add
from overlays.flash import Flash
from overlays.star_drive import StarDrive
from overlays.ripple import Ripple
import math


class OverlayInfo:
    # FIXME add keyword?
    def __init__(self, time, overlay):
        self.overlay = overlay
        self.max_contribution = 0.0
        self.start_time = time

    def get_overlaid_colour(self, colour, led, time):
        contribution = self.overlay.get_overlaid_colour(colour, led, time - self.start_time)

        total_contribution = 0

        for channel in contribution:
            total_contribution += math.fabs(channel)

        self.max_contribution = max(total_contribution, self.max_contribution)

        return contribution

    def get_max_contribution(self):
        max_contribution = self.max_contribution
        self.max_contribution = 0.0
        return max_contribution


class OverlayHandler:
    def __init__(self):
        self.epsilon = 10
        self.min_time = 2
        self.active_overlays = list()

    def update(self, time):
        self.active_overlays = list(overlay for overlay in self.active_overlays if time - overlay.start_time < self.min_time or overlay.get_max_contribution() > self.epsilon)

    def receive_command(self, command, time):
        if command["type"] == "overlay":
            if command["name"] == "flash":
                self.active_overlays.append(OverlayInfo(time, Flash(command["args"])))

            elif command["name"] == "star_drive":
                self.active_overlays.append(OverlayInfo(time, StarDrive(command["args"])))

            elif command["name"] == "ripple":
                self.active_overlays.append(OverlayInfo(time, Ripple(command["args"])))

            else:
                raise Exception("OverlayHandler: unknown overlay {}".format(command["name"]))

        else:
            raise Exception("OverlayHandler: unknown command type {}".format(command["type"]))

    def calculate_overlaid_colour(self, led, time):
        colour = led.colour

        for overlay in self.active_overlays:
            colour = overlay.get_overlaid_colour(colour, led, time)

        return colour
