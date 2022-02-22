from patterns.pattern import Pattern
import random
import numpy as np
import math


class MakeMeOneWithEverything(Pattern):
    def __init__(self, fixture):
        self._active_swooshes = []

        # sane defaults
        self._shimmer_level = 128
        self._white_level = 16
        self._swoosh_interval = 15

        self._time_factor = 1.0/50
        self._space_factor = 1.0

        self._next_swoosh = random.gauss(self._swoosh_interval, self._swoosh_interval / 4)

        self.cache_positions(fixture.leds)

    def cache_positions(self, pixels):
        self._origin_deltas = np.array(list(pixel.coord.get_delta("global") for pixel in pixels))
        self._local_phi = np.array(list(pixel.coord.get("local", "spherical").phi for pixel in pixels))
        self._local_theta = np.array(list(pixel.coord.get("local", "spherical").theta for pixel in pixels))
        self._global_theta = np.array(list(pixel.coord.get("global", "spherical").theta for pixel in pixels))

    def set_vars(self, command):
        self._shimmer_level = command.get("shimmer_level", self._shimmer_level)
        self._white_level = command.get("white_level", self._white_level)
        self._swoosh_interval = command.get("swoosh_interval", self._swoosh_interval)

    def update(self, leds, time, palette_handler, palette_name):
        if time > self._next_swoosh:
            self._next_swoosh = time + random.gauss(self._swoosh_interval, self._swoosh_interval)

            # TODO add starting angle
            # time, direction (phi or theta), swoosh speed between 2 and 5
            # only do theta swooshes for now
            self._active_swooshes.append((time, 1, random.random()*1 + 0.25, random.random()*2*math.pi))
            # self._active_swooshes.append((time, random.randrange(0, 2), random.random()*1 + 0.25, random.random()*2*math.pi))

        self._active_swooshes = list(swoosh for swoosh in self._active_swooshes if time - swoosh[0] < 30)
        pass

    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        mangled_deltas = np.maximum(self._origin_deltas + np.sin(self._global_theta + time/20 * (math.sin(time/7)/6 + 1))/2, 0)

        rgb = np.zeros((len(leds), 3))
        rgb[..., 0] = np.sin(-time / -2 + mangled_deltas * (5 + np.cos(-time / 2 + mangled_deltas) + 0.25))
        rgb[..., 1] = np.sin(-time / -2 + mangled_deltas * (5 + np.cos(-time / 2.2 + mangled_deltas))) + 0.25
        rgb[..., 2] = np.sin(-time / -2 + mangled_deltas * (5 + np.cos(-time / 2.5 + mangled_deltas))) + 0.25

        rgb *= self._shimmer_level

        w_major = self._white_level + np.sin(-time / -8 + self._origin_deltas / 3) * self._shimmer_level
        w_minor = np.sin(-time / -10 + self._origin_deltas / 1.4) * self._shimmer_level / 4
        intensity = np.sum(rgb, 1)

        w = w_major + w_minor - intensity

        w *= 0.5
        w += 0.25

        swoosh_level = np.zeros(len(leds))

        for swoosh in self._active_swooshes:
            time_since_swoosh = time-swoosh[0]

            distances_behind_swoosh = np.zeros(len(leds))

            if swoosh[1] == 0:
                distances_behind_swoosh = time_since_swoosh + swoosh[3] - self._local_phi

            elif swoosh[1] == 1:
                distances_behind_swoosh = time_since_swoosh + swoosh[3] - self._local_theta

            # while min(distances_behind_swoosh) < 0:
            distances_behind_swoosh %= 2*math.pi

            distances_behind_swoosh = np.maximum(distances_behind_swoosh, 1.0)

            intensity = 1.0 / max(time_since_swoosh / 3, 1)

            if time_since_swoosh < 1.0:
                intensity = time_since_swoosh

            swoosh_level += (1.0 / distances_behind_swoosh) * intensity


        # print(f"max swoosh level {max(swoosh_level)}")
        w = np.maximum(w, np.minimum(swoosh_level, 1)*64)

        raw_colours = palette_handler.sample_radial_all(self._origin_deltas, time, self._space_factor, self._time_factor, palette_name).astype(np.float32)

        rgb /= 2
        rgb += raw_colours/2

        rgb += w[:,np.newaxis]
        rgb *= (swoosh_level[:,np.newaxis] + 1)
        return rgb

    @staticmethod
    def inverse_square(x, y, exponent):
        return 1.0 / max(abs(x - y) ** exponent, 0.001)
