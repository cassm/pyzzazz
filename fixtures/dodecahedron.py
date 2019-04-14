from fixtures.led_fixture import LedFixture
from fixtures.led_fixture import Led
from common.coord import Coordinate
from common.coord import Spherical
from common.coord import Cartesian
import math

class Dodecahedron(LedFixture):
    def __init__(self, config, sender, overlay_handler):
        # dodecahedrons always have 60 pixels
        config["num_pixels"] = 60

        self.validate_config(config)

        LedFixture.__init__(self, config, sender, overlay_handler)

        led_spherical_local_coords = ((60,   6),  (20,  30),  (45,  48),  (75,  18), (100, 348),
                                     (300,   6), (260, 348), (285,  18), (315,  48), (340,  30),
                                     (180, 328), (140, 333), (165, 300), (195, 300), (220, 333),
                                     (120, 318),  (95, 338), (109, 238), (131, 258), (145, 288),
                                      (71,  58),  (49,  78),  (35, 108),  (60, 138),  (85, 158),
                                      (25,  63),  (00,  68), (335,  63), (249,  96),  (11,  96),
                                     (311,  78), (289,  58), (275, 158), (300, 138), (325, 108),
                                     (265, 338), (240, 318), (215, 288), (229, 258), (251, 238),
                                     (191, 276), (169, 243), (155, 248), (180, 243), (205, 276),
                                     (135, 228), (105, 198),  (80, 168), (120, 186), (160, 210),
                                      (40, 153),  (15, 120), (345, 120), (320, 153),   (5, 148),
                                     (280, 168), (255, 198), (225, 228), (200, 210), (240, 186))

        fixture_origin = Cartesian(*config.get("location"))

        for coord in led_spherical_local_coords:
            led_local_spherical = Spherical(r=config["radius"], theta=math.radians(coord[0]), phi=math.radians(coord[1]))
            led_coord = Coordinate(local_origin=fixture_origin, local_spherical=led_local_spherical)
            self.leds.append(Led(led_coord, [0.0, 0.0, 0.0]))

    def validate_config(self, config):
        if "radius" not in config.keys():
            raise Exception("Dodecahedron: config contains no radius")
