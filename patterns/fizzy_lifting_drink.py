from patterns.pattern import Pattern
import numpy as np
import math


# this is lifted from opc's raver_plaid example
class FizzyLiftingDrink(Pattern):
    def __init__(self, leds):
        self._led_deltas = np.array(list(led.coord.get_delta("global") for led in leds), dtype=np.float16)

    def get_pixel_colours(self, leds, time, palette_handler, palette_name):
        # how many sine wave cycles are squeezed into our n_pixels
        # 24 happens to create nice diagonal stripes on the wall layout
        freq_r = 24
        freq_g = 24
        freq_b = 24

        # how many seconds the color sine waves take to shift through a complete cycle
        speed_r = 7
        speed_g = -13
        speed_b = 19

        t = time * 5

        pct = (self._led_deltas * 77) % 37

        blackstripes = np.cos((pct - t*0.05) * math.pi*2) * 1.5
        blackstripes_offset = np.cos((pct/60.0 - 0.9) * math.pi*2) * 1.75 + 1.75
        blackstripes = np.clip(1.0, 0.0, blackstripes_offset + blackstripes)

        r = blackstripes * np.cos(pct * freq_r + t / speed_r)
        g = blackstripes * np.cos(pct * freq_g + t / speed_g)
        b = blackstripes * np.cos(pct * freq_b + t / speed_b)

        output = np.array(list([r[i], g[i], b[i]] for i in range(len(leds))))

        output += 1
        output *= 127

        return output
