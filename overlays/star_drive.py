from overlays.overlay import Overlay
from common.utils import nonzero
from common.utils import clamp
import numpy as np
import math


class StarDrive(Overlay):
    def __init__(self, args):
        Overlay.__init__(self, args)
        self.intensity = 0.0
        self.global_z = {}

    def get_overlaid_colours(self, colours, leds, time_since_start, fixture_name):
        if fixture_name not in self.global_z.keys():
            self.global_z[fixture_name] = np.array(list(led.coord.get("global", "cartesian").z for led in leds))

        self.intensity = 1.0/nonzero((time_since_start * 0.5) ** 2)

        effective_intensity = min(1.0, self.intensity)

        fade_level = np.sin(self.global_z[fixture_name]*2 - time_since_start*1.0 + math.pi*1.5) + 1.0
        np.clip(fade_level, 0.0, 1.0)

        warp_core_level = np.sin(self.global_z[fixture_name] * 25 - time_since_start*8) / 1.5 + 0.5
        np.clip(warp_core_level, 0.0, 1.0)

        fade_level *= effective_intensity

        warp_core_level *= fade_level * 1.4

        fade_level = fade_level[:len(colours)]
        warp_core_level = warp_core_level[:len(colours)]

        fade_level = fade_level[:,np.newaxis]
        warp_core_level = warp_core_level[:,np.newaxis]

        return colours * (1-fade_level) + (colours + 16*effective_intensity) * fade_level * warp_core_level

