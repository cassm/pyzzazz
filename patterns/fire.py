from patterns.pattern import Pattern
from common.utils import nonzero
import numpy as np
import random
import math


class Fire(Pattern):
    def __init__(self, leds, sample_radial=False):
        self.next_spark = 0.0
        self.spark_interval = 0.2
        self.fixture_offset = random.random() * 10
        self.pixel_info = list()
        self.sample_radial = sample_radial

        self.cache_positions(leds)

    def cache_positions(self, leds):
        max_delta = max(led.coord.get_delta("local") for led in leds)
        min_delta = min(led.coord.get_delta("local") for led in leds)
        delta_conversion_factor = 1.0 / (max_delta - min_delta)

        max_z = max(led.coord.get("local", "cartesian").z for led in leds)
        min_z = min(led.coord.get("local", "cartesian").z for led in leds)
        z_conversion_factor = 1.0 / (max_z - min_z)

        self.spark_intensity = np.zeros(len(leds))
        self.last_sparked = np.zeros(len(leds))
        self.local_phi = np.array(list(led.coord.get("local", "spherical").phi for led in leds))
        self.global_x = np.array(list(led.coord.get("global", "cartesian").x for led in leds))

        if self.sample_radial:
            self.normalised_offset = np.array(list((led.coord.get_delta("local") - min_delta) * delta_conversion_factor for led in leds))
        else:
            self.normalised_offset = np.array(list((-led.coord.get("local", "cartesian").z - min_z) * z_conversion_factor for led in leds))

    def update(self, leds, time, palette_handler, palette_name):
        if time > self.next_spark:
            self.next_spark = time + random.gauss(self.spark_interval, self.spark_interval / 4.0)
            spark = random.randrange(0,len(leds))
            self.last_sparked[spark] = time
            self.spark_intensity[spark] = random.gauss(1.0/8.0, 1.0/16.0)

    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        time_since_spark = np.maximum(1.0, time - self.last_sparked)
        spark_val = 1.0 / time_since_spark

        time_sine = math.sin(-time + 0.03 * self.fixture_offset) + math.sin(time / -(0.4 + 0.02 * self.fixture_offset)) / 4
        space_sine = np.sin(self.local_phi) / 3 + np.sin(time / -2 + self.global_x)

        total_sine_val = (time_sine + space_sine) / 16.0
        palette_position = self.normalised_offset + spark_val + total_sine_val
        palette_position = np.clip(1.0, 0.0, palette_position)

        return palette_handler.sample_positional_all(palette_position, "fire")
