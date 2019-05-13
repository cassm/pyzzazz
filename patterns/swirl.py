from patterns.pattern import Pattern
import numpy as np
import math


class Swirl(Pattern):
    def __init__(self, leds):
        self._time_factor = 1.0/50
        self._space_factor = 1.0
        self.cache_positions(leds)

    def cache_positions(self, leds):
        self._led_deltas = np.array(list(led.coord.get_delta("global") for led in leds), dtype=np.float16)
        self._led_thetas = np.array(list(led.coord.get("global", "spherical").theta for led in leds), dtype=np.float)
        self._theta_offsets = self._led_thetas * 0.5
        self._theta_offsets += self._led_deltas

        while np.min(self._theta_offsets) < 0:
            self._theta_offsets += 2*math.pi


    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        raw_colours = palette_handler.sample_radial_all(self._theta_offsets, time, self._space_factor, self._time_factor, palette_name).astype(np.float16)
        # raw_colours *= 0.7  # account for increased overall brightness
        raw_colours *= np.sin(self._theta_offsets*6 - (time*self._time_factor) * 24)[:,np.newaxis]/3 + 0.66

        return raw_colours
