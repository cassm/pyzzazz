from operator import add
from overlays.flash import Flash
from overlays.star_drive import StarDrive
from overlays.ripple import Ripple
from overlays.spark_shower import SparkShower
from overlays.hue_shift import HueShift
import numpy as np
import time


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
        print (self.max_contribution_per_led)
        max_contribution_per_led = self.max_contribution_per_led
        self.max_contribution_per_led = 0.0
        return max_contribution_per_led


class OverlayHandler:
    def __init__(self):
        self.epsilon = 10
        self.min_time = 5
        self.active_overlays = list()

    def update(self):
        self.active_overlays = list(overlay for overlay in self.active_overlays if time.time() - overlay.start_time < self.min_time or overlay.get_max_contribution_per_led() > self.epsilon)
        print(len(self.active_overlays))

    def receive_command(self, command):
        if command["type"] == "overlay":
            if command["name"] == "flash":
                self.active_overlays.append(OverlayInfo(Flash(command["args"])))

            elif command["name"] == "star_drive":
                self.active_overlays.append(OverlayInfo(StarDrive(command["args"])))

            elif command["name"] == "ripple":
                self.active_overlays.append(OverlayInfo(Ripple(command["args"])))

            elif command["name"] == "spark_shower":
                self.active_overlays.append(OverlayInfo(SparkShower(command["args"])))

            elif command["name"] == "hue_shift":
                self.active_overlays.append(OverlayInfo(HueShift(command["args"])))

            else:
                raise Exception("OverlayHandler: unknown overlay {}".format(command["name"]))

        else:
            raise Exception("OverlayHandler: unknown command type {}".format(command["type"]))

    def calculate_overlaid_colours(self, leds, colours, fixture_name):
        overlaid_colours = colours

        for overlay in self.active_overlays:
            overlaid_colours = overlay.get_overlaid_colours(overlaid_colours, leds, fixture_name)

        return overlaid_colours
