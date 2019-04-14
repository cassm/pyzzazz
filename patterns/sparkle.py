from patterns.pattern import Pattern
import random


class SparkleRecord:
    def __init__(self):
        self.time = 0
        self.colour = [0.0, 0.0, 0.0]


class Sparkle(Pattern):
    def __init__(self, num_leds):
        self._sparkle_info = [SparkleRecord() for _ in range(num_leds)]

        # sane defaults
        self._max_sparkles_percent = 8
        self._sparkle_probability = 0.05
        self._background_brightness = 0.5

        self._last_refresh = 0
        self._nominal_fps = 30

        self._time_divisor = 125
        self._space_divisor = 2

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
                self._sparkle_info[index].time = time - 0.5  # reduce time at full brightness
                self._sparkle_info[index].colour = palette_handler.sample_radial(leds[index].coord.get_delta("global"), time, self._space_divisor, self._time_divisor, palette_name)

    def get_pixel_colour(self, pixels, index, time, palette_handler, palette_name, master_brightness):
        # do not allow zero, because we divide by this
        time_delta = max(time - self._sparkle_info[index].time, 0.001)

        # do not allow brightness to exceed 1 to avoid distortion
        sparkle_brightness = min(1.0 / time_delta, 1.0)
        sparkle_value = list(channel * sparkle_brightness for channel in self._sparkle_info[index].colour)
        background_colour = palette_handler.sample_radial(pixels[index].coord.get_delta("global"), time, self._space_divisor, self._time_divisor, palette_name)
        background_colour = list(channel * self._background_brightness for channel in background_colour)

        total_value = list(map(max, sparkle_value, background_colour))
        return list(channel * master_brightness for channel in total_value)

