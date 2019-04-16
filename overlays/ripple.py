from overlays.overlay import Overlay
from common.utils import nonzero
from common.utils import clamp
import math


class Ripple(Overlay):
    def __init__(self, args):
        Overlay.__init__(self, args)
        self.intensities = {}

    def get_overlaid_colour(self, colour, led, time_since_start):
        intensity_smoothness = 0.5
        front_speed = 1.5
        front_progress = front_speed * time_since_start

        delay = 0.5

        front_progress -= delay

        if led not in self.intensities.keys():
            self.intensities[led] = 0.0

        time_since_front = max(0.0, front_progress - led.coord.get_delta("global"))

        front_intensity = 1.0/nonzero(time_since_front/2)

        if front_progress < led.coord.get_delta("global"):
            time_until_front = led.coord.get_delta("global") - front_progress
            front_intensity = 1.0 - nonzero(min(1.0, time_until_front/delay))

        self.intensities[led] = self.intensities[led] * intensity_smoothness + front_intensity * (1.0-intensity_smoothness)

        ripple_level = math.sin(led.coord.get_delta("global")*30 - time_since_start*front_speed)

        colour_factor = 1.0 + ripple_level*min(self.intensities[led], 1.0)

        return [channel * colour_factor for channel in colour]

