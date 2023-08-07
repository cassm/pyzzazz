from handlers.connections.redis_handler import RedisHandler
from fixtures.fixture import Fixture
from fixtures.led_fixture import LedFixture
from fixtures.bunting_polygon import BuntingPolygon
import inspect
import json
import datetime
import socket

UDP_PORT = 5005

class NodeSock:
    def __init__(self, ip_addr):
        addr = socket.getaddrinfo(ip_addr, 5005, socket.AF_INET, socket.SOCK_DGRAM)[0]
        self.sock = socket.socket(*addr[:3])
        self.sock.connect(addr[4])
        self.ip_addr = ip_addr

class StateHandler:
    def __init__(self, ):
        self.node_socks = {}
        self.redis = RedisHandler.get_instance()
        self.last_frame = None
        self.ip_map = {}

    def update_ips(self):
        self.ip_map = RedisHandler.try_command(self.redis.hgetall, 'pyzzazz:mac2ip')

    def update_colours(self, fixtures):
        # TODO keep as np array until last stage
        colours = []
        for x in fixtures:
            if isinstance(x, LedFixture):
                colours.extend(x.get_pixels(force_rgb=True).tolist())

        # prep for bytification
        # colours = [min(255, max(0, int(colours[i]))) for i in colours]
        # colours = bytes(colours)

        colours = [round(i/255.0, 3) for i in colours]
        colours = [colours[i:i+3] for i in range(0, len(colours), 3)]

        RedisHandler.try_command(self.redis.set, 'pyzzazz:leds:colours', json.dumps(colours))

    def refresh_sock(self, node):
        if node not in self.node_socks:
            self.node_socks[node] = NodeSock(self.ip_map[node])
        elif self.node_socks[node].ip_addr != self.ip_map[node]:
            self.node_socks[node].sock.close()
            self.node_socks[node] = NodeSock(self.ip_map[node])

    def control_nodes(self, nodeMapping):
        for node in nodeMapping.keys():
            cmd = RedisHandler.try_command(self.redis.rpop, f"pyzzazz:clients:{node}:cmd")
            if cmd is not None:
                if cmd == "PING":
                    self.send_node_cmd(node, "P")
                elif cmd == "RESET":
                    self.send_node_cmd(node, "R")
                elif cmd == "CLEAR":
                    self.send_node_cmd(node, "C")
                elif cmd == "COLOUR_MODE_RGB":
                    self.send_node_cmd(node, "4")
                elif cmd == "COLOUR_MODE_RGBW":
                    self.send_node_cmd(node, "3")
                else:
                    print(f"received unknown cmd for {node}: {cmd}")


    def update_nodes(self, fixtures):
        nodeMapping = RedisHandler.try_command(self.redis.hgetall, 'pyzzazz:clients')
        self.control_nodes(nodeMapping)

        for x in fixtures:
            if isinstance(x, LedFixture):
                pixels = x.get_pixels(force_rgb=True).tolist()
                dead_pixels = [1,1,1]*x.dead_pixels
                pixels = dead_pixels + pixels
                pixels = [ord("F")] + [max(0, min(255, int(ch))) for ch in pixels]

                pixels_bytes = bytes(pixels)

                for node in nodeMapping.keys():
                    if nodeMapping[node] == x.name:
                        if node in self.ip_map:
                            self.refresh_sock(node)
                            # print(f"{x.name}:{len(pixels)}:{len(pixels_bytes)}")
                            # print(f"sending {len(pixels_bytes)} to {self.ip_map[node]}:{UDP_PORT}")
                            try:
                                self.node_socks[node].sock.sendto(pixels_bytes, (self.ip_map[node], UDP_PORT))
                            except Exception as e:
                                print(e)
                    #     RedisHandler.try_command(self.redis.publish, f"pyzzazz:clients:{node}:leds", pixels_bytes)
    def send_node_cmd(self, node, cmd):
        print(f"cmd {node}::{cmd}")
        if node in self.ip_map:
            self.refresh_sock(node)
            # print(f"{x.name}:{len(pixels)}:{len(pixels_bytes)}")
            # print(f"sending {len(pixels_bytes)} to {self.ip_map[node]}:{UDP_PORT}")
            try:
                self.node_socks[node].sock.sendto(bytes([ord(cmd[0])]), (self.ip_map[node], UDP_PORT))
            except Exception as e:
                print(e)

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

