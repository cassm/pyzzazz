from pattern import Pattern
import math


class Smooth(Pattern):
    def __init__(self):
        self._time_divisor = 50
        self._space_divisor = 1

    def update(self, leds, time, palette):
        return

    def get_pixel_colour(self, pixels, index, time, palette):
        pos = pixels[index].coordinate.get_global_cartesian().list()
        space_delta = math.sqrt(pos[0]**2 + pos[1]**2 + pos[2]**2)
        return palette.sample_radial(space_delta, time, self._space_divisor, self._time_divisor)

