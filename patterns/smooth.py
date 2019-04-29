from patterns.pattern import Pattern
import numpy as np
import math


class Smooth(Pattern):
    def __init__(self, leds):
        self._time_factor = 1.0/50
        self._space_factor = 1.0
        self._led_deltas = np.array(list(led.coord.get_delta("global") for led in leds), dtype=np.float16)

    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        # def get_pixel_colour(self, pixels, index, time, palette_handler, palette_name, master_brightness):
        #     space_delta = pixels[index].coord.get_delta("global")
        #
        offsets_phi_component = np.array(list(math.sin(led.coord.get("global", "spherical").phi + time/6) / 2 + 0.9 for led in leds))
        offsets_theta_component = np.array(list(math.sin(led.coord.get("global", "spherical").theta + time/6) / 2 + 0.9 for led in leds))

        offsets = np.sin(offsets_phi_component + offsets_theta_component + time)
        offsets *= (math.sin(time/15.8) + 1) / 8
        offsets /= 4

        raw_colours = palette_handler.sample_radial_all(self._led_deltas + offsets, time, self._space_factor, self._time_factor, palette_name).astype(np.float16)
        raw_colours *= 0.7  # account for increased overall brightness

        return raw_colours
