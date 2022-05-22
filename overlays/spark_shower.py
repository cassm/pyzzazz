from overlays.overlay import Overlay
import numpy as np
import random
import time


class SparkShower(Overlay):
    def __init__(self, args):
        self.last_sparkles = {}
        self._sparkle_probability = args.get("sparkle_probability", 0.025)
        self.deltas = {}
        self.colour_factors = {}

    def get_overlaid_colours(self, colours, leds, time_since_start, fixture_name):
        # TODO cache colours and calc mode over all fixtures
        # todo k means clustering dominant colours

        if fixture_name not in self.last_sparkles.keys():
            self.deltas[fixture_name] = np.array(list(led.coord.get_delta("global") for led in leds))
            self.last_sparkles[fixture_name] = np.zeros(len(leds))
            self.colour_factors[fixture_name] = np.random.normal(1.0, 0.1, (len(leds), 3))

        # determine sparkle front probability
        front_speed = 1.0
        head_start = 0.5
        front_progress = front_speed * time_since_start + head_start

        time_since_front = front_progress - self.deltas[fixture_name]
        time_since_front = np.maximum(1, time_since_front)

        front_intensity = 1.0 / (time_since_front * 0.5)

        front_intensity[self.deltas[fixture_name] > front_progress] = 0

        # spawn new sparkles
        faded_probability = self._sparkle_probability * front_intensity

        for i in range(len(leds)):
            if random.random() < faded_probability[i]:
                self.last_sparkles[fixture_name][i] = time.time()

        time_since_sparkles = np.maximum(1.0, time.time() - self.last_sparkles[fixture_name])
        sparkle_intensities = 1.0 / np.maximum(0.5, time_since_sparkles / 1.5)
        sparkle_intensities *= (1.0 / np.maximum(1.0, time_since_front / 1))

        sparkle_colours = np.array(list([246, 101 + 101 * (1.0 / max(1.0, time_since_front[i] / 2)), 74] for i in range(len(leds))))
        sparkle_colours *= self.colour_factors[fixture_name]
        sparkle_colours *= sparkle_intensities[:,np.newaxis]

        np.clip(sparkle_colours, 0.0, 255.0)

        sparkle_colours = sparkle_colours[:len(colours)]

        return np.maximum(colours, sparkle_colours)
