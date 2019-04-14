from fixtures.fixture import Fixture
from patterns.sparkle import Sparkle
from patterns.fizzy_lifting_drink import FizzyLiftingDrink
from patterns.make_me_one_with_everything import MakeMeOneWithEverything
from patterns.fire import Fire
from patterns.smooth import Smooth
from operator import add


class Led:
    def __init__(self, coord, colour=[0.0, 0.0, 0.0]):
        self.colour = colour
        self.overlaid_colour = colour
        self.coord = coord


class LedFixture(Fixture):
    def __init__(self, config, senders, overlay_handler):
        self.validate_config(config)

        Fixture.__init__(self, config, overlay_handler)

        self.pattern = ""
        self.patterns = {}
        self.leds = []

        self.geometry = config.get("geometry", "No geometry present in fixture definition")
        self.pixel_type = config.get("pixel_type", "No pixel_type present in fixture definition")
        self.num_pixels = config.get("num_pixels", "No num_pixels present in fixture definition")
        self.senders = senders
        self.line = config.get("line", "No line present in fixture definition")

    def validate_config(self, config):
        if "pixel_type" not in config.keys():
            raise Exception("LedFixture: config contains no pixel_type")

        if "geometry" not in config.keys():
            raise Exception("LedFixture: config contains no geometry")

        if "line" not in config.keys():
            raise Exception("LedFixture: config contains no line")

    def receive_command(self, command, value):
        if command["type"] == "pattern":
            self.pattern = command["name"]
            self.patterns[self.pattern].set_vars(command["args"])

        elif command["type"] == "palette":
            self.palette_name = command["name"]

        else:
            raise Exception("LedFixture: unknown command type {}".format(command["type"]))

    def register_command(self, command):
        if command["type"] == "pattern":
            if command["name"] not in self.patterns:
                if command["name"] == "smooth":
                    self.patterns["smooth"] = Smooth()

                elif command["name"] == "sparkle":
                    self.patterns["sparkle"] = Sparkle(len(self.leds))

                elif command["name"] == "fizzy_lifting_drink":
                    self.patterns["fizzy_lifting_drink"] = FizzyLiftingDrink()

                elif command["name"] == "make_me_one_with_everything":
                    self.patterns["make_me_one_with_everything"] = MakeMeOneWithEverything()

                elif command["name"] == "fire":
                    self.patterns["fire"] = Fire(self.leds)

                else:
                    raise Exception("LedFixture: unknown pattern {}".format(command["name"]))

        elif command["type"] == "palette":
            # handled, but nothing to do
            pass

        else:
            raise Exception("LedFixture: unknown command type {}".format(command["type"]))

    def send(self):
        if len(self.leds) > 0:
            for sender in self.senders:
                sender.send(self.line, self.get_pixels(force_rgb=sender.is_simulator))

    def update(self, time, palette, smoothness, master_brightness):
        if self.pattern not in self.patterns.keys():
            raise Exception("LedFixture: unknown pattern {}".format(self.pattern))

        # update all patterns so they are in a sensible state when we switch
        for pattern in self.patterns.values():
            pattern.update(self.leds, time, palette, self.palette_name)

        if smoothness < 0 or smoothness > 1:
            raise Exception("illegal smoothness value of {}".format(smoothness))

        for index, led in enumerate(self.leds):
            old_value = led.colour
            new_value = self.patterns[self.pattern].get_pixel_colour(self.leds, index, time, palette, self.palette_name, master_brightness)

            led.colour = [old_value[i] * smoothness + new_value[i] * (1.0 - smoothness) for i in range(3)]
            # led.colour = old_value * smoothness + new_value * (1.0 - smoothness)
            led.overlaid_colour = self.overlay_handler.calculate_overlaid_colour(led, time)

    def get_pixels(self, force_rgb=False):
        if force_rgb or self.pixel_type == "rgb":
            return self.get_byte_values("rgb", list(led.overlaid_colour for led in self.leds))
        else:
            return self.get_byte_values("grbw", list(led.overlaid_colour for led in self.leds))

    def get_byte_values(self, format, pixels):
        byte_value_buffer = list()

        for pixel in pixels:
            current_pixel = list()

            for channel in pixel:
                current_pixel.append(max(0, min(255, int(channel))))

            if format == "grbw":
                w = min(current_pixel)

                byte_value_buffer.append(current_pixel[1])
                byte_value_buffer.append(current_pixel[0])
                byte_value_buffer.append(current_pixel[2])
                byte_value_buffer.append(w)

            else:
                byte_value_buffer.extend(current_pixel)

        while len(byte_value_buffer) % 3:
            byte_value_buffer.append(0)

        return byte_value_buffer

    def get_coords(self):
        return list(list(led.coord.get("global", "cartesian")) for led in self.leds)

    def add_cartesian(self, vector):
        for led in self.leds:
            led.coord.add_cartesian(vector)

    def rotate_phi_global(self, angle):
        for led in self.leds:
            led.coord.rotate_theta_global(angle)

    def rotate_theta_global(self, angle):
        for led in self.leds:
            led.coord.rotate_theta_global(angle)

    def rotate_phi_local(self, angle):
        for led in self.leds:
            led.coord.rotate_theta_local(angle)

    def rotate_theta_local(self, angle):
        for led in self.leds:
            led.coord.rotate_theta_local(angle)

    def has_sender(self, name):
        return name in list(sender.name for sender in self.senders)
