from handlers.connections.redis_handler import RedisHandler
from fixtures.fixture import Fixture
from fixtures.led_fixture import LedFixture
from fixtures.bunting_polygon import BuntingPolygon
import inspect
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

    def update_fixtures(self, fixtures):
        fixture_tree = {}

        # build class and instance tree
        for x in fixtures:
            inheritance = [cls.__name__ for cls in inspect.getmro(type(x))]
            inheritance.reverse()

            # assume we're inheriting from fixture
            inheritance = inheritance[inheritance.index(Fixture.__name__):]

            # walk down fixture inheritance path, creating branches as necessary
            ptr = fixture_tree
            for y in inheritance:
                if y not in ptr:
                    ptr[y] = {}

                ptr = ptr[y]

            # add instances leaf if any exist
            if 'instances' not in ptr:
                ptr['instances'] = []

            ptr['instances'].append(x.name)

        self.redis.set('pyzzazz:fixtures', json.dumps(fixture_tree))

    def update_patterns(self, pattern_handler):
        self.redis.set('pyzzazz:patterns', json.dumps(list(pattern_handler.get_patterns().keys())))

    def update_palettes(self, palette_handler):
        self.redis.set('pyzzazz:palettes', json.dumps(palette_handler.get_palette_names()))

    def update_overlays(self, overlay_handler):
        self.redis.set('pyzzazz:overlays', json.dumps(list(overlay_handler.get_overlays().keys())))

