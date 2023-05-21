from handlers.connections.redis_handler import RedisHandler
from fixtures.fixture import Fixture
from fixtures.led_fixture import LedFixture
from fixtures.bunting_polygon import BuntingPolygon
import inspect
import json
import datetime


class StateHandler:
    def __init__(self, ):
        self.redis = RedisHandler.get_instance()
        self.last_frame = None

    def update_colours(self, fixtures):
        # TODO keep as np array until last stage
        colours = []
        for x in fixtures:
            if isinstance(x, LedFixture):
                colours.extend(x.get_pixels(force_rgb=True).tolist())

        # rounding to 3 dec places drastically reduces network transfer volume, as this is transferred as a string
        colours = [round(i/255.0, 3) for i in colours]

        colours = [colours[i:i+3] for i in range(0, len(colours), 3)]

        RedisHandler.try_command(self.redis.set, 'pyzzazz:leds:colours', json.dumps(colours))

    def update_nodes(self, fixtures):
        nodeMapping = RedisHandler.try_command(self.redis.hgetall, 'pyzzazz:clients')

        for x in fixtures:
            if isinstance(x, LedFixture):
                pixels = x.get_pixels(force_rgb=True).tolist()
                pixels_hex = [hex(max(0, min(255, y)))[2:].zfill(2) for y in pixels]
                pixels_str = ":".join(pixels_hex)

                for node in nodeMapping.keys():
                    if nodeMapping[node] == x.name:
                        RedisHandler.try_command(self.redis.set, f"pyzzazz:clients:{node}:leds", pixels_str)

    def update_coords(self, fixtures):
        coords = []
        for x in fixtures:
            if isinstance(x, LedFixture):
                fixture_coords = x.get_coords()
                if isinstance(x, BuntingPolygon):
                    fixture_coords.pop()
                coords.extend(fixture_coords)

        RedisHandler.try_command(self.redis.set, 'pyzzazz:leds:coords', json.dumps(coords))

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

        RedisHandler.try_command(self.redis.set, 'pyzzazz:fixtures', json.dumps(fixture_tree))

    def update_fps(self):
        new_frame = datetime.datetime.now()
        if self.last_frame:
            interval_secs = (new_frame - self.last_frame).total_seconds()
            frame_data = {
                'fps': round(1.0/interval_secs, 1),
            }
            RedisHandler.try_command(self.redis.set, 'pyzzazz:fps', json.dumps(frame_data))

        self.last_frame = new_frame

    def update_patterns(self, pattern_handler):
        patterns = list(pattern_handler.get_patterns().keys())

        # map video requires arguments and needs its own section
        patterns.remove('map_video')

        RedisHandler.try_command(self.redis.set, 'pyzzazz:patterns', json.dumps(patterns))

    def update_palettes(self, palette_handler):
        RedisHandler.try_command(self.redis.set, 'pyzzazz:palettes', json.dumps(palette_handler.get_palette_names()))

    def update_overlays(self, overlay_handler):
        RedisHandler.try_command(self.redis.set, 'pyzzazz:overlays', json.dumps(list(overlay_handler.get_overlays().keys())))

    def update_sliders(self, settings_handler):
        RedisHandler.try_command(self.redis.set, 'pyzzazz:sliders', json.dumps(settings_handler.get_sliders()))

