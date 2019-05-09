from overlays.overlay import Overlay
import numpy as np


class Ripple(Overlay):
    def __init__(self, args):
        Overlay.__init__(self, args)
        self.deltas = {}
        self.intensities = {}

    def get_overlaid_colours(self, colours, leds, time_since_start, fixture_name):
        if fixture_name not in self.deltas.keys():
            self.deltas[fixture_name] = np.array(list(led.coord.get_delta("global") for led in leds))
            self.intensities[fixture_name] = np.zeros(len(leds))

        front_speed = 3.0
        front_progress = front_speed * time_since_start

        delay = 0.0

        front_progress -= delay

        time_since_front = front_progress - self.deltas[fixture_name]
        time_since_front = np.maximum(1, time_since_front)

        front_intensity = 1.0 / (time_since_front / 4.5)

        front_intensity[self.deltas[fixture_name] > time_since_front] = 0

        ripple_level = np.sin(self.deltas[fixture_name]*7.5 - time_since_start*front_speed)
        ripple_level *= front_intensity
        ripple_level *= -1

        ripple_level += 1

        ripple_level = ripple_level[:len(colours)]

        return colours * ripple_level[:,np.newaxis]
