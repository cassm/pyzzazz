import os
import imageio
from common.utils import nonzero


class PaletteHandler:
    def __init__(self, palette_path):
        self.palette_path = os.path.join(os.getcwd(), palette_path)
        self.palettes = {}

        if not os.path.isdir(palette_path):
            raise Exception("ERROR: the directory {} does not exist".format(palette_path))

        self.standard_palette_len = 1000
        self.parse_palette_files()

        assert len(self.palettes.keys()) > 0, "No parsable palette files present!"

        self.palette_space_factor = 3.0
        self.palette_time_factor = 1.0
        self.master_palette_name = list(self.palettes.keys())[0]

    def set_master_palette_name(self, name):
        self.master_palette_name = name

    def parse_palette_files(self):
        for filename in os.listdir(self.palette_path):
            if filename.endswith(".bmp"):
                try:
                    image = imageio.imread(os.path.join(self.palette_path, filename))
                    palette_pixels_per_image_pixel = float(self.standard_palette_len) / float(len(image[0]))

                    rgb_buffer = list()

                    # ensure all palettes are exactly the same len
                    for index, pixel in enumerate(image[0]):
                        if index*palette_pixels_per_image_pixel >= len(rgb_buffer):
                            rgb_buffer.append(pixel.tolist())

                    while len(rgb_buffer) < self.standard_palette_len:
                        rgb_buffer.append(rgb_buffer[-1])

                    rgb_buffer = rgb_buffer[:self.standard_palette_len]

                    print("Palette: parsed palette file {} of length {}".format(filename, len(rgb_buffer)))

                    self.palettes[filename[:-4]] = rgb_buffer

                except:
                    print("Palette: failed to parse palette file {}".format(filename))

    def set_palette_space_factor(self, value):
        self.palette_space_factor = (1.0 / nonzero(value)) / 12.0  # expect 0 to 1

    def set_palette_time_factor(self, value):
        self.palette_time_factor = value * 2.0  # expect 0 to 1

    def sample_positional(self, position, palette_name):
        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        assert 0.0 <= position <= 1.0, "sample_positional: position must be between 0 and 1"

        index = int(position * self.standard_palette_len-1)
        return self.palettes[palette_to_use][index]

    def sample_radial(self, space_delta, time_delta, space_factor, time_factor, palette_name):
        assert 0 <= time_factor <= 1.0, "Time factor must be between 0 and 1"
        assert 0 <= space_factor <= 1.0, "Space factor must be between 0 and 1"

        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        total_progress = int((space_delta * self.palette_space_factor * space_factor
                              - time_delta * self.palette_time_factor * time_factor) * self.standard_palette_len)

        total_progress %= self.standard_palette_len

        return self.palettes[palette_to_use][total_progress]
