from fixtures.led_fixture import LedFixture
from fixtures.led_fixture import Led
from common.coord import Coordinate
from common.coord import Cartesian
from common.coord import Cylindrical
import math


class Cylinder(LedFixture):
    def __init__(self, config, senders, overlay_handler):
        self.validate_config(config)

        num_pixels = config.get("num_leds")
        num_turns = config.get("num_turns")
        radius = config.get("radius")
        height = config.get("height")
        fixture_origin = Cartesian(*config.get("location"))

        theta_per_pixel = num_turns * 2*math.pi / num_pixels
        z_per_pixel = height/num_pixels

        LedFixture.__init__(self, config, senders, overlay_handler)

        for i in range(num_pixels):
            theta = (i * theta_per_pixel) % (2*math.pi)
            z = i * z_per_pixel - height/2
            led_local_cylindrical = Cylindrical(r=radius, theta=theta, z=z)
            flat_mapping=[theta / 2*math.pi, z / height]
            led_coord = Coordinate(local_origin=fixture_origin, local_cylindrical=led_local_cylindrical)
            self.leds.append(Led(led_coord, flat_mapping=flat_mapping))

    def validate_config(self, config):
        if "radius" not in config.keys():
            raise Exception("Cylinder: config contains no radius")

        if "height" not in config.keys():
            raise Exception("Cylinder: config contains no height")

        if "num_turns" not in config.keys():
            raise Exception("Cylinder: config contains no num_turns")
