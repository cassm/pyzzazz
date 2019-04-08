from fixture import Fixture


class Led:
    def __init__(self, coordinate, colour=Colour()):
        self.colour = colour
        self.coordinate = coordinate


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
        return self.r - o.r, self.g - o.g, self.b - o.b

    def __isub__(self, o):
        self.r -= o.r
        self.g -= o.g
        self.b -= o.b
        return self

    def max(self, o):
        return max(self.r, o.r), max(self.g, o.g), max(self.b, o.b)


class LedFixture(Fixture):
    def __init__(self, config, sender):
        Fixture.__init__(self, config)
        self.geometry = config.get("geometry", "No geometry present in fixture definition")
        self.num_pixels = config.get("num_pixels", "No num_pixels present in fixture definition")
        self.sender = sender
        self.line = config.get("line", "No line present in fixture definition")

        self.leds = []

    def send(self):
        self.sender.send(self.line, self.leds)

    def get_pixels(self):
        return list(led.colour for led in self.leds)

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
