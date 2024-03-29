import os
import imageio
from common.utils import nonzero
import numpy as np


class PaletteHandler:
    def __init__(self, palette_path):
        self.palette_path = os.path.join(os.getcwd(), palette_path)

        self.palettes = np.array([[[]]])
        self.palette_names = list()

        if not os.path.isdir(palette_path):
            raise Exception("ERROR: the directory {} does not exist".format(palette_path))

        self.standard_palette_len = 1000
        self.parse_palette_files()

        assert len(self.palettes) > 0, "No parsable palette files present!"

        self.palette_space_factor = 3.0
        self.palette_time_factor = 1.0
        self.master_palette_name = self.palette_names[0]

    def get_palette_names(self):
        return self.palette_names

    def set_master_palette_name(self, name):
        self.master_palette_name = name

    def parse_palette_files(self):
        palettes = list()

        for filename in os.listdir(self.palette_path):
            if filename.endswith(".bmp"):
                try:
                    image = imageio.imread(os.path.join(self.palette_path, filename))
                    indices = list(int(i * (len(image[0]) - 1) / self.standard_palette_len) for i in range(self.standard_palette_len))

                    rgb_buffer = np.array(image[0])[indices].astype(np.float32)

                    print("Palette: parsed palette file {} of length {}".format(filename, len(rgb_buffer)))

                    self.palette_names.append(filename[:-4])

                    palettes.append(rgb_buffer)

                except Exception as e:
                    print("Palette: failed to parse palette file {}".format(filename))
                    raise e

        self.palettes = np.array(palettes).astype(np.float32)

    def set_palette_space_factor(self, value):
        self.palette_space_factor = (1.0 / max(value, 0.01)) / 12.0  # expect 0 to 1

    def set_palette_time_factor(self, value):
        self.palette_time_factor = value * 2.0  # expect 0 to 1

    def sample_positional(self, position, palette_name):
        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        palette_index = self.palette_names.index(palette_to_use)

        assert 0.0 <= position <= 1.0, "sample_positional: position must be between 0 and 1"

        index = int(position * (self.standard_palette_len-1))
        return self.palettes[palette_index][index]

    def sample_positional_all(self, positions, palette_name):
        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        palette_index = self.palette_names.index(palette_to_use)

        positions %= 1.0

        indices = positions * (self.standard_palette_len-1)
        return self.palettes[palette_index][list(indices.astype(int))].astype(np.float32)

    def sample_radial(self, space_delta, time_delta, space_factor, time_factor, palette_name):
        assert 0 <= time_factor <= 1.0, "Time factor must be between 0 and 1"
        assert 0 <= space_factor <= 1.0, "Space factor must be between 0 and 1"

        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        palette_index = self.palette_names.index(palette_to_use)

        if palette_index == -1:
            raise Exception("unknown palette name ", palette_to_use)

        time_delta *= self.palette_time_factor * time_factor

        total_progress = space_delta * self.palette_space_factor * space_factor
        total_progress -= time_delta
        total_progress *= self.standard_palette_len

        while total_progress < 0:
            total_progress += self.standard_palette_len

        total_progress %= self.standard_palette_len

        return self.palettes[palette_index][int(total_progress)]

    def sample_radial_all(self, space_deltas, time_delta, space_factor, time_factor, palette_name):

        assert 0 <= time_factor <= 1.0, "Time factor must be between 0 and 1"
        assert 0 <= space_factor <= 1.0, "Space factor must be between 0 and 1"
        palette_to_use = palette_name

        if not palette_name:
            palette_to_use = self.master_palette_name

        palette_index = self.palette_names.index(palette_to_use)

        if palette_index == -1:
            raise Exception("unknown palette name ", palette_to_use)

        time_delta *= self.palette_time_factor * time_factor

        total_progress = np.array((space_deltas * (self.palette_space_factor * space_factor)))
        total_progress -= time_delta
        total_progress %= 1
        total_progress *= self.standard_palette_len

        while min(total_progress) < 0:
            total_progress += self.standard_palette_len

        total_progress %= self.standard_palette_len

        return self.palettes[palette_index][list(total_progress.astype(int))].astype(np.float32)
