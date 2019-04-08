from fixture import Fixture


class Colour:
    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b

        self.__radd__ = self.__add__
        self.__rsub__ = self.__sub__

    def __add__(self, o):
        return self.r + o.r, self.g + o.g, self.b + o.b

    def __iadd__(self, o):
        self.r += o.r
        self.g += o.g
        self.b += o.b
        return self

    def __sub__(self, o):
        return max(self.r - o.r, 0), max(self.g - o.g, 0), max(self.b - o.b, 0)

    def __isub__(self, o):
        self.r = max(self.r - o.r, 0)
        self.g = max(self.g - o.g, 0)
        self.b = max(self.b - o.b, 0)
        return self

    def max(self, o):
        return max(self.r, o.r), max(self.g, o.g), max(self.b, o.b)


class Led:
    def __init__(self, coordinate, colour=Colour()):
        self.colour = colour
        self.coordinate = coordinate


class LedFixture(Fixture):
    def __init__(self, config, sender):
        self.validate_config(config)

        Fixture.__init__(self, config)

        self.geometry = config.get("geometry", "No geometry present in fixture definition")
        self.num_pixels = config.get("num_pixels", "No num_pixels present in fixture definition")
        self.sender = sender
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
        self.sender.send(self.line, self.leds)

    def get_pixels(self):
        return list(led.colour for led in self.leds)

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
