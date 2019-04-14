from overlays.overlay import Overlay
import math

class StarDrive(Overlay):
    def get_overlaid_colour(self, colour, led, time_since_start):
        intensity = math.sin(time_since_start/2)

        fade_level = math.sin(led.coord.get("global", "cartesian").z * 2 - time_since_start*4)/2 + 0.5

        warp_core_level = math.sin(led.coord.get("global", "cartesian").z * 15 + time_since_start*4)/2 + 0.7
        warp_core_level *= fade_level

        fade_level *= intensity
        warp_core_level *= intensity
        return [channel * (1 - fade_level) + 255*warp_core_level for channel in colour]

