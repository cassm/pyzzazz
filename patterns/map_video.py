from patterns.pattern import Pattern
import numpy as np


class MapVideo(Pattern):
    def __init__(self, pixels, image_src):
        self.video_handler = image_src
        self.cache_positions(pixels)

    def cache_positions(self, pixels):
        self.flat_mappings = np.array(list(pixel.flat_mapping for pixel in pixels))

    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        return self.video_handler.sample(self.flat_mappings)
