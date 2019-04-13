from patterns.pattern import Pattern
from common.utils import nonzero
import random
import math


class PixelInfo:
    def __init__(self, normalised_z):
        self.spark_intensity = 0.0
        self.last_sparked = 0.0
        self.normalised_z = normalised_z


class Fire(Pattern):
    def __init__(self, leds):
        self.next_spark = 0.0
        self.spark_interval = 0.2
        self.fixture_offset = random.random() * 10
        self.pixel_info = list()

        max_z = max(led.coord.get("local", "cartesian").z for led in leds)
        min_z = min(led.coord.get("local", "cartesian").z for led in leds)
        z_conversion_factor = 1.0 / (max_z - min_z)

        for i in range(len(leds)):
            normalised_z = (-leds[i].coord.get("local", "cartesian").z - min_z) * z_conversion_factor
            self.pixel_info.append(PixelInfo(normalised_z))

    def update(self, leds, time, palette_handler, palette_name):
        if time > self.next_spark:
            self.next_spark = time + random.gauss(self.spark_interval, self.spark_interval / 4.0)
            spark = random.choice(self.pixel_info)
            spark.last_sparked = time
            spark.intensity = random.gauss(1.0/8.0, 1.0/16.0)

    def get_pixel_colour(self, pixels, index, time, palette_handler, master_brightness, palette_name):
        assert index < len(self.pixel_info), "out of bounds led index"
        time_since_spark = nonzero(time - self.pixel_info[index].last_sparked)

        spark_val = min(1.0 / time_since_spark, 1.0)

        sine_vals = [math.sin(-time + 0.03 * self.fixture_offset),
                     math.sin(time / -(0.4 + 0.02 * self.fixture_offset)) / 4,
                     math.sin(pixels[index].coord.get("local", "spherical").phi) / 3,
                     math.sin(time / -2 + pixels[index].coord.get("global", "cartesian").x)]

        total_sine_val = sum(sine_vals) / 16.0

        palette_position = max(0, min(1, self.pixel_info[index].normalised_z + spark_val + total_sine_val))

        return palette_handler.sample_positional(palette_position, "fire")
