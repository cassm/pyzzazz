from fixtures.led_fixture import LedFixture
from fixtures.led_fixture import Led
from common.coord import Cartesian
from common.coord import Cylindrical
from common.coord import Coordinate
from common.utils import nonzero
import numpy as np
import math


class Arch(LedFixture):
    def __init__(self, config, senders, overlay_handler, video_handler, calibration_handler):
        self.validate_config(config)

        LedFixture.__init__(self, config, senders, overlay_handler, video_handler, calibration_handler)

        self.pattern_map_by_polar = True

        height = config.get("height")
        r = config.get("r")
        theta = config.get("theta")
        width = config.get("width")
        floor = config.get("floor")

        tangent_angle = theta + math.pi/2

        local_origin = Cylindrical(r=r, theta=theta, z=height/2).to_cartesian()
        start = Coordinate(local_cylindrical=Cylindrical(r=width/2, theta=tangent_angle, z=0), local_origin=local_origin).get("global", "cartesian")
        end = Coordinate(local_cylindrical=Cylindrical(r=width/2, theta=tangent_angle + math.pi, z=0), local_origin=local_origin).get("global", "cartesian")

        leds = list()

        for i in range(self.num_pixels):
            proportion_along_string = float(i) / self.num_pixels

            x = start.x * (1.0 - proportion_along_string) + end.x * proportion_along_string
            y = start.y * (1.0 - proportion_along_string) + end.y * proportion_along_string
            z = math.sin(proportion_along_string*math.pi) * height + floor

            fixture_origin = Cartesian(x=x, y=y, z=height/2)

            led_coord = Coordinate(local_origin=fixture_origin, local_cartesian=Cartesian(x-local_origin.x, y-local_origin.y, z-local_origin.z))
            leds.append(Led(led_coord))

        self.leds = np.array(leds)

        for i, led in enumerate(self.leds):
            # between 0 and 1
            # edge of 3/4 of a circle
            proportion_along_string = float(i) / self.num_pixels
            map_coord = Cylindrical(r=1.0, theta=(math.pi*1.5) * proportion_along_string, z=0)
            map_x = map_coord.to_cartesian().x
            map_y = map_coord.to_cartesian().y

            led.flat_mapping = (map_x, map_y)

    def validate_config(self, config):
        pass
