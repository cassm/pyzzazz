from patterns.pattern import Pattern
from common.utils import nonzero
import numpy as np
import random


class SparkleRecord:
    def __init__(self):
        self.time = 0
        self.colour = [0.0, 0.0, 0.0]


class Sparkle(Pattern):
    def __init__(self, leds):
        # sane defaults
        self._max_sparkles_percent = 4
        self._sparkle_probability = 0.025
        self._background_brightness = 0.5

        self._last_refresh = 0
        self._nominal_fps = 30

        self._time_factor = 1.0 / 50
        self._space_factor = 1.0

        self.cache_positions(leds)

    def cache_positions(self, leds):
        num_pixels = len(leds)
        self._sparkle_times = np.zeros(num_pixels, dtype=np.float32)
        self._sparkle_colours = np.zeros((num_pixels, 3), dtype=np.float32)
        self._led_deltas = np.array(list(led.coord.get_delta("global") for led in leds), dtype=np.float32)

    def set_vars(self, command):
        self._max_sparkles_percent = command.get("max_sparkles_percent", self._max_sparkles_percent)
        self._sparkle_probability = command.get("sparkle_probability", self._sparkle_probability)
        self._background_brightness = command.get("background_brightness", self._background_brightness)

    def update(self, leds, time, palette_handler, palette_name):
        max_sparkles = int(self._max_sparkles_percent / 100.0 * len(leds))

        # normalise probability in relation to frame interval, so we get more sparkles when time is moving faster
        frame_interval = time - self._last_refresh
        nominal_normal_frame_interval = 1.0 / self._nominal_fps
        frame_duration_proportion = frame_interval / nominal_normal_frame_interval
        normalised_sparkle_probability = self._sparkle_probability * frame_duration_proportion

        for i in range(max_sparkles):
            if random.random() < normalised_sparkle_probability:
                index = random.randrange(0, len(leds))
                self._sparkle_times[index]= time - 0.5  # reduce time at full brightness
                self._sparkle_colours[index] = palette_handler.sample_radial(self._led_deltas[index], time, self._space_factor, self._time_factor, palette_name)

    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        # do not allow zero, because we divide by this
        time_deltas = time - self._sparkle_times
        time_deltas *= 2
        time_deltas = np.clip(999, 0.75, time_deltas)
        sparkle_intensities = 1.0 / time_deltas.astype(np.float32)
        # sparkle_intensities = np.clip(1.0, 0.0, sparkle_intensities)
        sparkle_colours = self._sparkle_colours*sparkle_intensities[:,np.newaxis]

        # background_colours = []
        # for i in range(len(leds)):
        #     background_colours.append(palette_handler.sample_radial(self._led_deltas[i]*20, time*2.5, self._space_factor, self._time_factor, palette_name))
        # background_colours = np.array(background_colours, dtype=np.float32)
        # print(type(self._background_brightness))
        # background_colours *= self._background_brightness

        background_colours = palette_handler.sample_radial_all(self._led_deltas, time, self._space_factor, self._time_factor, palette_name).astype(np.float32)
        background_colours *= self._background_brightness
        return np.maximum(sparkle_colours, background_colours)

