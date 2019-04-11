from pattern import Pattern
from colour import Colour
import random


class SparkleRecord:
    def __init__(self):
        self.time = 0
        self.colour = Colour(0, 0, 0)


class Sparkle(Pattern):
    def __init__(self, num_leds, max_sparkles, sparkle_probability, background_brightness):
        self._sparkle_info = [SparkleRecord() for _ in range(num_leds)]
        self._max_sparkles = max_sparkles
        self._sparkle_probability = sparkle_probability
        self._background_brightness = background_brightness

        self._time_divisor = 50
        self._space_divisor = 1

    def update(self, leds, time, palette):
        for i in range(self._max_sparkles):
            if random.random() < self._sparkle_probability:
                index = random.randrange(0, len(leds))
                # print("sparkle at {} on {} out of {}".format(time, index, len(leds)))
                self._sparkle_info[index].time = time
                self._sparkle_info[index].colour = palette.sample_radial(leds[index].coord.get_global_delta(), time, self._space_divisor, self._time_divisor)

    def get_pixel_colour(self, pixels, index, time, palette):
        # do not allow zero, because we divide by this
        time_delta = max(time - self._sparkle_info[index].time, 0.001)

        # do not allow brightness to exceed 1 to avoid distortion
        sparkle_brightness = min(1.0 / time_delta, 1.0)
        sparkle_value = self._sparkle_info[index].colour * sparkle_brightness
        background_colour = palette.sample_radial(pixels[index].coord.get_global_delta(), time, self._space_divisor, self._time_divisor)
        background_colour *= self._background_brightness

        return sparkle_value.channelwise_max(background_colour)

