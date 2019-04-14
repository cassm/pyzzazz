from patterns.pattern import Pattern
import random
import math


class MakeMeOneWithEverything(Pattern):
    def __init__(self):
        self._active_swooshes = []

        # sane defaults
        self._shimmer_level = 128
        self._white_level = 64
        self._swoosh_interval = 15

        self._next_swoosh = random.gauss(self._swoosh_interval, self._swoosh_interval / 4)

    def set_vars(self, command):
        self._shimmer_level = command.get("shimmer_level", self._shimmer_level)
        self._white_level = command.get("white_level", self._white_level)
        self._swoosh_interval = command.get("swoosh_interval", self._swoosh_interval)

    def update(self, leds, time, palette_handler, palette_name):
        if time > self._next_swoosh:
            self._next_swoosh = time + random.gauss(self._swoosh_interval, self._swoosh_interval / 4)

            # TODO add starting angle
            # time, direction (phi or theta), swoosh speed between 2 and 5
            self._active_swooshes.append((time, random.randrange(1, 3), random.random()*3 + 2))

        self._active_swooshes = list(swoosh for swoosh in self._active_swooshes if time - swoosh[0] < 30)
        pass

    def get_pixel_colour(self, pixels, index, time, palette_handler, palette_name, master_brightness):
        pixel = pixels[index]
        origin_delta = pixel.coord.get_delta("global")

        r = max(math.sin(-time / -2 + origin_delta * (5 + math.cos(-time / 2 + origin_delta))) * self._shimmer_level, 0)
        g = max(math.sin(-time / -2 + origin_delta * (5 + math.cos(-time / 2.2 + origin_delta))) * self._shimmer_level, 0)
        b = max(math.sin(-time / -2 + origin_delta * (5 + math.cos(-time / 2.5 + origin_delta))) * self._shimmer_level, 0)
        w = self._white_level + math.sin(-time / -8 + origin_delta / 3) * self._shimmer_level + math.sin(-time / -10 + origin_delta / 1.4) * self._shimmer_level / 4 - sum((r, g, b))
        w *= 0.9

        swoosh_level = 0.0

        for swoosh in self._active_swooshes:
            time_since_swoosh = time-swoosh[0]

            distance_behind_swoosh = time_since_swoosh*swoosh[2] - pixel.coord.get("local", "spherical")[swoosh[1]]

            while distance_behind_swoosh < 0:
                distance_behind_swoosh += 2*math.pi

            swoosh_level += min(1.0 / max(distance_behind_swoosh, 0.001), 1)

        w = max(w, swoosh_level * 255)

        return list(channel * master_brightness for channel in [r+w, g+w, b+w])

    @staticmethod
    def inverse_square(x, y, exponent):
        return 1.0 / max(abs(x - y) ** exponent, 0.001)
