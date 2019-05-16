from overlays.overlay import Overlay
from common.utils import rgb_to_hsv, hsv_to_rgb


class HueShift(Overlay):
    def __init__(self, args):
        self.min_deltas = {}

    def get_overlaid_colours(self, colours, leds, time_since_start, fixture_name):
        if fixture_name not in self.min_deltas.keys():
            self.min_deltas[fixture_name] = min(list(led.coord.get_delta("global") for led in leds))

        front_speed = 0.5
        band_width = 2.5
        headstart = 0.75  # flip first fixture straight away

        front_progress = front_speed * time_since_start + headstart

        if front_progress - band_width < self.min_deltas[fixture_name] < front_progress:
            proportion_through_band = (front_progress - self.min_deltas[fixture_name]) / band_width

            shift_amount = 0.5 * (1.0 - proportion_through_band)

            hsv = rgb_to_hsv(colours)
            hsv[..., 0] = (hsv[..., 0]+shift_amount) % 1.0
            return hsv_to_rgb(hsv).astype('float32')

        else:
            return colours
