from overlays.overlay import Overlay
from common.utils import nonzero
from common.utils import clamp
import math

class StarDrive(Overlay):
    def __init__(self, args):
        Overlay.__init__(self, args)
        self.intensity = 0.0

    def get_overlaid_colour(self, colour, led, time_since_start):
        intensity_smoothness = 0.5
        self.intensity = self.intensity * intensity_smoothness + 1.0/nonzero(time_since_start * 0.75) * (1.0-intensity_smoothness)

        effective_intensity = min(1.0, self.intensity)

        fade_level = clamp(math.sin(led.coord.get("global", "cartesian").z * 1 - time_since_start*2)/2 + 0.75, 0.0, 1.0)

        warp_core_level = clamp(math.sin(led.coord.get("global", "cartesian").z * 25 - time_since_start*8)/1.5 + 0.5, 0.0, 1.0)
        warp_core_level *= fade_level * 1.2

        fade_level *= effective_intensity
        warp_core_level *= effective_intensity
        return [channel * (1 - fade_level) + (channel+64)*warp_core_level for channel in colour]

