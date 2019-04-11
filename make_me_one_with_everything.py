from pattern import Pattern
from colour import Colour
import random
import math


class MakeMeOneWithEverything(Pattern):
    def __init__(self, shimmer_level, white_level, swoosh_interval):
        self._active_swooshes = []
        self._shimmer_level = shimmer_level
        self._white_level = white_level
        self._swoosh_interval = swoosh_interval
        self._next_swoosh = random.gauss(self._swoosh_interval, self._swoosh_interval / 4)

    def update(self, leds, time, palette):
        if time > self._next_swoosh:
            self._next_swoosh = time + random.gauss(self._swoosh_interval, self._swoosh_interval / 4)

            # TODO add starting angle
            # time, direction (r, phi or theta), swoosh speed between 2 and 5
            self._active_swooshes.append((time, random.randrange(3), random.random()*3 + 2))

        self._active_swooshes = list(swoosh for swoosh in self._active_swooshes if time - swoosh[0] < 500)
        pass

    def get_pixel_colour(self, pixels, index, time, palette):
        pixel = pixels[index]
        origin_delta = pixel.coord.get_global_delta()

        r = max(math.sin(-time / -2 + origin_delta * (5 + math.cos(-time / 2 + origin_delta))) * self._shimmer_level, 0)
        g = max(math.sin(-time / -2 + origin_delta * (5 + math.cos(-time / 2.2 + origin_delta))) * self._shimmer_level, 0)
        b = max(math.sin(-time / -2 + origin_delta * (5 + math.cos(-time / 2.5 + origin_delta))) * self._shimmer_level, 0)
        w = self._white_level + math.sin(-time / -8 + origin_delta / 3) * self._shimmer_level + math.sin(-time / -10 + origin_delta / 1.4) * self._shimmer_level / 4 - sum((r, g, b))

        swoosh_level = 0.0

        for swoosh in self._active_swooshes:
            time_since_swoosh = time-swoosh[0]

            distance_behind_swoosh = time_since_swoosh*swoosh[2] - pixel.coord.get("local", "spherical")[swoosh[1]]

            while distance_behind_swoosh < 0:
                distance_behind_swoosh += 2*math.pi

            swoosh_level += min(1.0 / max(distance_behind_swoosh, 0.001), 1)

        w = max(w, swoosh_level * 255)

        # FIXME is suspect this is broken
        return Colour(r+w, g+w, b+w)

    @staticmethod
    def inverse_square(x, y, exponent):
        return 1.0 / max(abs(x - y) ** exponent, 0.001)
