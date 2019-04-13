from patterns.pattern import Pattern
import math


class Smooth(Pattern):
    def __init__(self):
        self._time_divisor = 50
        self._space_divisor = 1

    def update(self, leds, time, palette):
        return

    def get_pixel_colour(self, pixels, index, time, palette):
        space_delta = pixels[index].coord.get_delta("global")

        offset_phi_component = (math.sin(pixels[index].coord.get("global", "spherical").phi + time/6) / 2 + 0.9)
        offset_theta_component = (math.sin(pixels[index].coord.get("global", "spherical").theta + time/2.8) / 2 + 0.9)

        offset_space_component = offset_phi_component + offset_theta_component

        offset_time_component = time
        offset = math.sin(offset_space_component + offset_time_component)
        offset *= (math.sin(time/15.8) + 1) / 8
        offset /= 4
        space_delta += offset

        return palette.sample_radial(space_delta, time, self._space_divisor, self._time_divisor)

