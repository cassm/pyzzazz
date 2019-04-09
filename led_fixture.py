from fixture import Fixture
from sparkle import Sparkle
from smooth import Smooth
from colour import Colour


class Led:
    def __init__(self, coordinate, colour=Colour()):
        self.colour = colour
        self.coordinate = coordinate


class LedFixture(Fixture):
    def __init__(self, config, senders):
        self.validate_config(config)

        Fixture.__init__(self, config)

        self.geometry = config.get("geometry", "No geometry present in fixture definition")
        self.num_pixels = config.get("num_pixels", "No num_pixels present in fixture definition")
        self.senders = senders
        self.line = config.get("line", "No line present in fixture definition")

        self.leds = []

    def validate_config(self, config):
        if "geometry" not in config.keys():
            raise Exception("LedFixture: config contains no geometry")

        if "line" not in config.keys():
            raise Exception("LedFixture: config contains no line")

    def parse_command(self, command_string):
        pass

    def send(self):
        if len(self.leds) > 0:
            for sender in self.senders:
                sender.send(self.line, self.get_pixels())

    def get_pixels(self):
        return list((min(led.colour.r, 255), min(led.colour.g, 255), min(led.colour.b, 255)) for led in self.leds)

    def get_coords(self):
        return list(led.coordinate.get_global_cartesian().list() for led in self.leds)

    def add_cartesian(self, vector):
        for led in self.leds:
            led.coordinate.add_cartesian(vector)

    def rotate_phi_global(self, angle):
        for led in self.leds:
            led.coordinate.rotate_theta_global(angle)

    def rotate_theta_global(self, angle):
        for led in self.leds:
            led.coordinate.rotate_theta_global(angle)

    def rotate_phi_local(self, angle):
        for led in self.leds:
            led.coordinate.rotate_theta_local(angle)

    def rotate_theta_local(self, angle):
        for led in self.leds:
            led.coordinate.rotate_theta_local(angle)

    def has_sender(self, name):
        return name in list(sender.name for sender in self.senders)
