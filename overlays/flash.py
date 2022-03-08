from overlays.overlay import Overlay
from common.utils import nonzero


class Flash(Overlay):
    def __init__(self, args):
        self.decay_factor = args.get('decay_factor', 1.0)

    def get_overlaid_colours(self, colours, leds, time_since_start, fixture_name):
        factor = min(2.0, 1.0 / nonzero((time_since_start + 0.25) * self.decay_factor))

        return colours * max(factor, 1)
