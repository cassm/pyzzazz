import os
import imageio
from common.utils import nonzero


class PaletteHandler:
    def __init__(self, palette_path):
        self.palette_path = os.path.join(os.getcwd(), palette_path)
        self.palettes = {}

        if not os.path.isdir(palette_path):
            raise Exception("ERROR: the directory {} does not exist".format(palette_path))

        self.parse_palette_files()

        assert len(self.palettes.keys()) > 0, "No parsable palette files present!"

        self.space_per_palette = 3.0
        self.time_per_palette = 1.0
        self.master_palette_name = list(self.palettes.keys())[0]

    def set_master_palette_name(self, name):
        self.master_palette_name = name

    def parse_palette_files(self):
        for filename in os.listdir(self.palette_path):
            print(filename)
            if filename.endswith(".bmp"):
                try:
                    image = imageio.imread(os.path.join(self.palette_path, filename))

                    rgb_buffer = list()

                    for pixel in image[0]:
                        rgb_buffer.append(pixel.tolist())

                    print("Palette: parsed palette file {} of length {}".format(filename, len(rgb_buffer)))

                    self.palettes[filename[:-4]] = rgb_buffer

                except:
                    print("Palette: failed to parse palette file {}".format(filename))

    def set_space_per_palette(self, value):
        self.space_per_palette = value * 6.0  # expect 0 to 1

    def set_time_per_palette(self, value):
        self.time_per_palette = value * 2.0  # expect 0 to 1

    def colour_correct(self, factors):
        self.rgb_buffer = list(list(cha * factors[i] for i, cha in enumerate(pix)) for pix in self.rgb_buffer)

    def sample_positional(self, position, palette_name):
        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        assert 0.0 <= position <= 1.0, "sample_positional: position must be between 0 and 1"

        index = int(position * (len(self.palettes[palette_to_use]) - 1))
        return self.palettes[palette_to_use][index]

    @profile
    def sample_radial(self, space_delta, time_delta, space_divisor, time_divisor, palette_name):
        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        while space_delta < 0:
            space_delta += self.space_per_palette

        while time_delta < 0:
            time_delta += self.time_per_palette

        space_delta /= nonzero(space_divisor)
        time_delta /= nonzero(time_divisor)

        # move forwards not backwards
        time_delta = 1-time_delta

        space_progress = space_delta / nonzero(self.space_per_palette)
        time_progress = time_delta / nonzero(self.time_per_palette)
        total_progress = (space_progress + time_progress) % 1.0

        total_index = int(total_progress * len(self.palettes[palette_to_use]))

        return self.palettes[palette_to_use][total_index]
