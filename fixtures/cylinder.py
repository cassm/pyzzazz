from fixtures.led_fixture import LedFixture
from fixtures.led_fixture import Led
from common.coord import Coordinate
from common.coord import Cartesian
from common.coord import Cylindrical
import numpy as np
import math


class Cylinder(LedFixture):
    def __init__(self, config, senders, overlay_handler, video_handler):
        self.validate_config(config)

        num_pixels = config.get("num_leds")
        num_turns = config.get("num_turns")
        radius = config.get("radius")
        height = config.get("height")
        fixture_origin = Cartesian(*config.get("location"))

        theta_per_pixel = num_turns * 2*math.pi / num_pixels
        z_per_pixel = height/num_pixels

        LedFixture.__init__(self, config, senders, overlay_handler, video_handler)

        angle_from_centre = fixture_origin.to_cylindrical().theta

        if fixture_origin.x < 0:
            angle_from_centre += math.pi

        print(fixture_origin)
        print("angle from centre {}".format(angle_from_centre))

        leds = list()

        for i in range(num_pixels):
            theta = (i * theta_per_pixel) % (2*math.pi)
            z = i * z_per_pixel - height/2
            led_local_cylindrical = Cylindrical(r=radius, theta=theta, z=z)

            mapping_angle = theta - angle_from_centre
            while mapping_angle < 0:
                mapping_angle += 2*math.pi
            mapping_angle %= (2*math.pi)

            flat_mapping=[mapping_angle / (2.0*math.pi), i * z_per_pixel / height]
            led_coord = Coordinate(local_origin=fixture_origin, local_cylindrical=led_local_cylindrical)
            leds.append(Led(led_coord, flat_mapping=flat_mapping))

        self.leds = np.array(leds)

    def validate_config(self, config):
        if "radius" not in config.keys():
            raise Exception("Cylinder: config contains no radius")

        if "height" not in config.keys():
            raise Exception("Cylinder: config contains no height")

        if "num_turns" not in config.keys():
            raise Exception("Cylinder: config contains no num_turns")
