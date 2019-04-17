from senders.sender_handler import SenderHandler
import openpixelcontrol.python.opc as opc
import subprocess
import json
import os
from pathlib import Path


class OpcSenderHandler(SenderHandler):

    def __init__(self, config, src_dir):
        SenderHandler.__init__(self, config)

        self.validate_config(config)

        self.ip = config.get("ip")
        self.port = config.get("port")
        self._client = opc.Client(":".join([self.ip, self.port]))
        self._previously_connected = False

        self._src_dir = src_dir
        self._layouts_dir = "{}/layouts".format(self._src_dir)

        if not os.path.isdir(self._layouts_dir):
            os.mkdir(self._layouts_dir)

        self._line_offsets = list()
        self._line_lengths = list()

        self._buffer = list()

    def validate_config(self, config):
        if "ip" not in config.keys():
            raise Exception("Sender: config contains no ip")

    def generate_layout_files(self, fixtures):
        fixtures_list = dict((fix.line, fix.get_coords()) for fix in fixtures if fix.has_sender(self.name))

        print("generating layout...")

        point_list = list()

        for line in range(max(fixtures_list.keys()) + 1):
            print("parsing fixture on line {}...".format(line))
            fixture_point_list = list({"point": led} for led in fixtures_list.get(line, []))
            point_list.extend(fixture_point_list)

            self._buffer.append([[0, 0, 0]] * len(fixture_point_list))

            self._line_offsets.append(sum(self._line_lengths))
            self._line_lengths.append(len(fixture_point_list))

        with open("{}/{}_layout.json".format(self._layouts_dir, self.name), "w") as f:
            f.write(json.dumps(point_list, indent=2))

        print("\n")

    def start(self):
        if self.is_simulator:
            args = list()
            args.append("{}/openpixelcontrol/bin/gl_server".format(self._src_dir))
            args.append("-l{}/{}_layout.json".format(self._layouts_dir, self.name))
            args.append("-p{}".format(self.port))

            print("Opening open pixel control simulation server...\n\n")
            return subprocess.Popen(args)

    def is_connected(self):
        if self._previously_connected:
            if self._client.can_connect():
                return True
            else:
                self._previously_connected = False
                print("OpcSender {}: Server disconnected on {}".format(self.name, self.port))
                return False
        else:
            if self._client.can_connect():
                self._previously_connected = True
                print("OpcSender {}: Connected to server on {}".format(self.name, self.port))
                return True
            else:
                return False

    def try_connect(self):
        return

    def send(self, line, byte_values):
        if line > len(self._line_offsets) or line < 0:
            raise Exception("Sender: send called on invalid line {}".format(line))

        pixels = list(byte_values[i:i+3] for i in range(0, len(byte_values), 3))

        if len(pixels) > self._line_lengths[line]:
            pixels = pixels[:self._line_lengths[line]]

        self._buffer[self._line_offsets[line]:self._line_offsets[line] + len(pixels)] = pixels

        if self.is_connected():
            self._client.put_pixels(self._buffer, channel=line+1)
