from pattern import Pattern
from colour import Colour
import random
import math


class MakeMeOneWithEverything(Pattern):
    def __init__(self, shimmer_level, white_level, swoosh_interval):
        self._active_swooshes = []
        self._next_swoosh = 0
        self._shimmer_level = shimmer_level
        self._white_level = white_level
        self._swoosh_interval = swoosh_interval

    def update(self, leds, time, palette):
        if time > self._next_swoosh:
            self._next_swoosh = time + random.gauss(self._swoosh_interval, self._swoosh_interval / 4)

            # time, direction (phi or theta)
            self._active_swooshes.append((time, random.randrange(2)))

        self._active_swooshes = list(swoosh for swoosh in self._active_swooshes if time - swoosh[0] < 500)

    def get_pixel_colour(self, pixels, index, time, palette):
        origin_delta = pixels[index].coordinate.get_global_delta()

        r = max(math.sin(time / -2 + origin_delta * (5 + math.cos(time / 2 + origin_delta))) * self._shimmer_level, 0)
        g = max(math.sin(time / -2 + origin_delta * (5 + math.cos(time / 2.2 + origin_delta))) * self._shimmer_level, 0)
        b = max(math.sin(time / -2 + origin_delta * (5 + math.cos(time / 2.5 + origin_delta))) * self._shimmer_level, 0)
        w = self._white_level + math.sin(time / -8 + origin_delta / 3) * self._shimmer_level + math.sin(time / -10 + origin_delta / 1.4) * self._shimmer_level / 4 - sum((r, g, b))

        swoosh_level = 0

        #TODO I think the swooshes are broken
        for swoosh in self._active_swooshes:
            swoosh_level += self.inverse_square(pixels[index].coordinate.get("local", "spherical").list()[swoosh[1]+1]+30, (time - swoosh[0])*2, 2.5)

        w = max(w, swoosh_level * 255)

        # FIXME is suspect this is broken
        return Colour(r+w, g+w, b+w)

    @staticmethod
    def inverse_square(x, y, exponent):
        return 1.0 / max(abs(x - y) ** exponent, 0.001)
