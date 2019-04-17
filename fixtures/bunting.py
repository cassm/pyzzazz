from fixtures.led_fixture import LedFixture
from fixtures.led_fixture import Led
from common.coord import Cartesian
from common.coord import Coordinate
import math


class Bunting(LedFixture):
    def __init__(self, config, senders, overlay_handler):
        self.validate_config(config)

        config["num_pixels"] = config.get("leds_per_strand") * config.get("num_strands")

        LedFixture.__init__(self, config, senders, overlay_handler)

        if config.get("arrangement") == "hexagon":
            self.pattern_map_by_polar = True

            radius = config.get("radius")
            diameter = radius * 2

            num_edges = 6
            edge_length = diameter/2.0
            perimeter = num_edges*edge_length

            length_per_strand = config.get("length_per_strand")
            num_strands = config.get("num_strands")
            total_strand_length = length_per_strand * num_strands

            if perimeter >= total_strand_length:
                raise Exception("Hexagon specified with diameter too great for length of strands. Perimeter = "
                                + str(perimeter) + " strand length " + str(total_strand_length))

            # calculate drop
            span = perimeter/num_edges
            length = total_strand_length/num_edges

            drop_at_centre = math.sqrt(length**2 - span**2)
            fixture_origin = Cartesian(*config.get("location"))

            vertices = list((radius * math.cos(math.pi / 3 * i),  radius * math.sin(math.pi / 3 * i)) for i in range(num_edges))

            horizontal_distance_between_pixels = total_strand_length / self.num_pixels

            for i in range(self.num_pixels):
                position_on_string = i * horizontal_distance_between_pixels
                edge_index = int((position_on_string / edge_length) % num_edges)
                position_on_edge = position_on_string % edge_length
                proportion_along_edge = position_on_edge / edge_length

                edge_start = vertices[edge_index]
                edge_end = vertices[(edge_index+1) % num_edges]

                x = edge_start[0] * proportion_along_edge + edge_end[0] * (1.0 - proportion_along_edge)
                y = edge_start[1] * proportion_along_edge + edge_end[1] * (1.0 - proportion_along_edge)

                # estimate catenary with sinusoidal curve
                z = -math.sin(proportion_along_edge * math.pi) * drop_at_centre

                led_coord = Coordinate(local_origin=fixture_origin, local_cartesian=Cartesian(x, y, z))
                self.leds.append(Led(led_coord))

            # add farthest point for sampling purposes
            if "farthest_point" in config.keys():
                self.leds.append(Led(Coordinate(local_origin=fixture_origin, local_cartesian=Cartesian(*config.get("farthest_point")))))


    def validate_config(self, config):
        if "length_per_strand" not in config.keys():
            raise Exception("LedFixture: config contains no length_per_strand")

        if "leds_per_strand" not in config.keys():
            raise Exception("LedFixture: config contains no leds_per_strand")

        if "num_strands" not in config.keys():
            raise Exception("LedFixture: config contains no num_strands")

        if "arrangement" not in config.keys():
            raise Exception("LedFixture: config contains no arrangement")

        if "arrangement" == "hexagon":
            if "radius" not in config.keys():
                raise Exception("LedFixture: config contains no radius")
