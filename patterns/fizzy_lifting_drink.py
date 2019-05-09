from patterns.pattern import Pattern
import numpy as np
import math


# this is lifted from opc's raver_plaid example
class FizzyLiftingDrink(Pattern):
    def __init__(self, leds):
        self._time_factor = 1.0/50
        self._space_factor = 1.0

        self._led_deltas = np.array(list(led.coord.get_delta("global") for led in leds), dtype=np.float16)
        self._led_thetas = np.array(list(led.coord.get("global", "spherical").theta for led in leds), dtype=np.float16)

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

        pct = (self._led_deltas * 77) % 37 + self._led_thetas

        blackstripes = np.cos((pct - t*0.05) * math.pi*2) * 1.5
        blackstripes_offset = np.cos((pct/60.0 - 0.9) * math.pi*2) * 1.75 + 1.75
        blackstripes = np.clip(1.0, 0.0, blackstripes_offset + blackstripes)

        r = blackstripes * np.cos(pct * freq_r + t / speed_r)
        g = blackstripes * np.cos(pct * freq_g + t / speed_g)
        b = blackstripes * np.cos(pct * freq_b + t / speed_b)

        # output = np.zeros((len(leds), 3), dtype=np.float16)
        # np.put_along_axis(output, [[0]] * num_leds, r, 1)
        # np.put_along_axis(output, [1], g, 1)
        # np.put_along_axis(output, [2], b, 1)
        output = np.array(list([r[i], g[i], b[i]] for i in range(len(leds))))

        output += 1
        output *= 127

        raw_colours = palette_handler.sample_radial_all(self._led_deltas, time, self._space_factor, self._time_factor, palette_name).astype(np.float16)
        raw_colours *= blackstripes[:,np.newaxis]

        return output * 0.5 + raw_colours * 0.5
        # return output * raw_colours / 2
