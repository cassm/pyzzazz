import os
import imageio
from common.colour import Colour


class Palette:
    def __init__(self, palette_path):
        palette_path = os.path.join(os.getcwd(), palette_path)

        if not os.path.isfile(palette_path):
            raise Exception("ERROR: the file {} does not exist".format(palette_path))

        self.rgb_buffer = []
        self.parse_file(palette_path)

        self.space_per_palette = 3.0
        self.time_per_palette = 1.0

    def nonzero(self, value):
        if value == 0.0:
            value += 0.0001

        return value

    def set_space_per_palette(self, value):
        self.space_per_palette = value * 6.0  # expect 0 to 1

    def set_time_per_palette(self, value):
        self.time_per_palette = value * 2.0  # expect 0 to 1

    def parse_file(self, palette_path):
        try:
            image = imageio.imread(palette_path)
            for pixel in image[0]:
                self.rgb_buffer.append(pixel.tolist())

        except:
            raise Exception("Palette: failed to parse palette file")

    def colour_correct(self, factors):
        self.rgb_buffer = list(list(cha * factors[i] for i, cha in enumerate(pix)) for pix in self.rgb_buffer)

    def sample_radial(self, space_delta, time_delta, space_divisor, time_divisor):
        while space_delta < 0:
            space_delta += self.space_per_palette

        while time_delta < 0:
            time_delta += self.time_per_palette

        space_delta /= self.nonzero(space_divisor)
        time_delta /= self.nonzero(time_divisor)

        # move forwards not backwards
        time_delta = 1-time_delta

        space_progress = space_delta / self.nonzero(self.space_per_palette)
        time_progress = time_delta / self.nonzero(self.time_per_palette)
        total_progress = (space_progress + time_progress) % 1.0

        total_index = int(total_progress * len(self.rgb_buffer))

        return Colour(*self.rgb_buffer[total_index])
