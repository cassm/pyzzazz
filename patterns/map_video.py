from patterns.pattern import Pattern
import numpy as np


class MapVideo(Pattern):
    def __init__(self, fixture):
        self.video_handler = fixture.video_handler
        self.cache_positions(fixture.leds)

    def cache_positions(self, pixels):
        self.flat_mappings = np.array(list(pixel.flat_mapping for pixel in pixels))

    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        return self.video_handler.sample(self.flat_mappings)
