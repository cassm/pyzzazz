from sender import Sender
import openpixelcontrol.python.opc as opc
import subprocess
import json
import os


class OpcSender(Sender):
    def __init__(self, config):
        Sender.__init__(self, config)

        self.validate_config(config)

        self.name = config.get("name")
        self.ip = config.get("ip")
        self.port = config.get("port")
        self.num_lines = config.get("num_lines")
        self._client = opc.Client(":".join([self.ip, self.port]))
        self._previously_connected = False

        #FIXME this is stupid
        self._src_dir = os.path.expanduser("~/PycharmProjects/pyzzazz")
        self._layouts_dir = "{}/layouts".format(self._src_dir)

        if not os.path.isdir(self._layouts_dir):
            os.mkdir(self._layouts_dir)

    def validate_config(self, config):
        if "ip" not in config.keys():
            raise Exception("Sender: config contains no ip")

        if config.get("num_lines") > 10:
            raise Exception("OpcSender: We only support a max of ten lines")

    def generate_layout_files(self, fixtures):
        fixtures_list = dict((fix.line, fix.get_coords()) for fix in fixtures if fix.has_sender(self.name))

        for line in range(self.num_lines):
            print("generating layouts/{}_{}.json...".format(self.name, line))

            point_list = list({"point": led} for led in fixtures_list.get(line, []))

            with open("{}/{}_{}.json".format(self._layouts_dir, self.name, line), "w") as f:
                f.write(json.dumps(point_list, indent=2))

        print("\n")

    def start(self):
        args = list()
        args.append("{}/openpixelcontrol/bin/gl_server".format(self._src_dir))

        for i in range(self.num_lines):
            args.append("-l{}/{}_{}.json".format(self._layouts_dir, self.name, i))

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

    def send(self, line, pixels):
        if line > self.num_lines or line < 0:
            raise Exception("Sender: send called on invalid line {}".format(line))

        if self.is_connected():
            self._client.put_pixels(pixels, channel=line+1)
