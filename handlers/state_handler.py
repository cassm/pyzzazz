from handlers.connections.redis_handler import RedisHandler
from fixtures.led_fixture import LedFixture
from fixtures.bunting_polygon import BuntingPolygon
import json


class StateHandler:
    def __init__(self, ):
        self.redis = RedisHandler.get_instance()

    def update_colours(self, fixtures):
        # TODO keep as np array until last stage
        colours = []
        for x in fixtures:
            if isinstance(x, LedFixture):
                colours.extend(x.get_pixels(force_rgb=True).tolist())

        colours = [i/255.0 for i in colours]

        colours = [colours[i:i+3] for i in range(0, len(colours), 3)]

        self.redis.set('pyzzazz:leds:colours', json.dumps(colours))

    def update_coords(self, fixtures):
        coords = []
        for x in fixtures:
            if isinstance(x, LedFixture):
                fixture_coords = x.get_coords()
                if isinstance(x, BuntingPolygon):
                    fixture_coords.pop()
                coords.extend(fixture_coords)

        self.redis.set('pyzzazz:leds:coords', json.dumps(coords))
