from fixtures.fixture import Fixture
import numpy as np
import math


class Led:
    def __init__(self, coord, flat_mapping=[0.0, 0.0]):
        self.coord = coord
        self.flat_mapping = flat_mapping


class SenderInfo:
    def __init__(self, sender, line):
        self.sender = sender
        self.line = line


class LedFixture(Fixture):
    def __init__(self, config, senders, overlay_handler, video_handler, calibration_handler):
        self.validate_config(config)

        Fixture.__init__(self, config, overlay_handler, video_handler, calibration_handler)

        self.geometry = config.get("geometry", "No geometry present in fixture definition")
        self.channel_order = config.get("channel_order", "No channel_order present in fixture definition")
        self.dead_pixels_start = config.get("dead_pixels_start", 0)
        self.dead_pixels_end = config.get("dead_pixels_end", 0)
        self.num_pixels = (config.get("num_pixels", 0) - self.dead_pixels_start) - self.dead_pixels_end
        self.senders_info = list(SenderInfo(sender[0], sender[1]) for sender in senders)

        # deal with hex values
        for sender_info in self.senders_info:
            if isinstance(sender_info.line, str):
                sender_info.line = int(sender_info.line, 16)

        self.power_budget = config.get("power_budget", None) # watts

        self.pattern = config.get("default_pattern")

        self.patterns = {}

        self.leds = np.array([])
        self.colours = np.zeros((self.num_pixels, 3), dtype=np.float32)
        self.overlaid_colours = np.zeros((self.num_pixels, 3), dtype=np.float32)

        self.pattern_map_by_polar = False

    def validate_config(self, config):
        if "default_pattern" not in config.keys():
            raise Exception("LedFixture: config contains no default_pattern")

        if "channel_order" not in config.keys():
            raise Exception("LedFixture: config contains no channel_order")

        if "geometry" not in config.keys():
            raise Exception("LedFixture: config contains no geometry")

    def toggle_calibrate(self):
        self.calibrate = not self.calibrate

    def receive_command(self, command, value):
        if command["type"] == "pattern":
            self.pattern = command["name"]
            self.patterns[self.pattern].set_vars(command["args"])

        elif command["type"] == "palette":
            self.palette_name = command["name"]

        else:
            raise Exception("LedFixture: unknown command type {}".format(command["type"]))

    def init_patterns(self, pattern_handler):
        for name, pattern in pattern_handler.get_patterns().items():
            self.patterns[name] = pattern(self)

    def send(self):
        if len(self.leds) > 0:
            for sender_info in self.senders_info:
                sender_info.sender.send(sender_info.line, self.get_pixels(force_rgb=sender_info.sender.is_simulator))

    def update(self, time, palette, smoothness, master_brightness):
        if self.calibration_handler.get_angle(self.name) != self.calibration_angle:
            angle_delta = self.calibration_handler.get_angle(self.name) - self.calibration_angle

            for led in self.leds:
                led.coord.rotate("theta", "local", angle_delta)

            for pattern in self.patterns.values():
                pattern.cache_positions(self.leds)

            self.calibration_angle = self.calibration_handler.get_angle(self.name)

        if self.pattern not in self.patterns.keys():
            raise Exception("LedFixture: unknown pattern {}".format(self.pattern))

        # update all patterns so they are in a sensible state when we switch
        for pattern in self.patterns.values():
            pattern.update(self.leds, time, palette, self.palette_name)

        if smoothness < 0 or smoothness > 1:
            raise Exception("illegal smoothness value of {}".format(smoothness))

        if self.calibrate:
            self.overlaid_colours = self.get_calibration_colours()

        else:
            new_colours = self.patterns[self.pattern].get_pixel_colours(self.leds, time, palette, self.palette_name)
            new_colours = new_colours[:len(self.colours)]
            self.colours = self.colours * smoothness + new_colours * (1.0 - smoothness)

            self.overlaid_colours = self.overlay_handler.calculate_overlaid_colours(self.leds, self.colours, self.name)
            self.overlaid_colours *= master_brightness

    def get_pixels(self, force_rgb=False):
        if force_rgb:
            return self.get_byte_values("rgb", self.overlaid_colours)
        else:
            return self.get_byte_values(self.channel_order, self.overlaid_colours)

    def get_calibration_colours(self):
        colours = np.zeros_like(self.overlaid_colours)

        if self.calibration_handler.get_selection() == self.name:
            thetas = np.array(list(led.coord.get("local", "spherical").theta for led in self.leds))
            thetas = thetas[:len(self.overlaid_colours)]
            thetas %= (2*math.pi)
            thetas -= math.pi
            thetas = np.abs(thetas)
            thetas -= math.pi / 2
            thetas *= (255.0 / (math.pi / 2.0))
            thetas = np.maximum(0, thetas)

            deltas = np.array(list(led.coord.get_delta("global") for led in self.leds))
            deltas = deltas[:len(self.overlaid_colours)]
            min_delta = np.min(deltas)
            max_delta = np.max(deltas)
            delta_range = max_delta - min_delta
            deltas -= min_delta
            deltas -= delta_range / 2
            deltas *= -1
            deltas *= (254 / (delta_range / 2))
            deltas = np.maximum(0, deltas)

            colours[...,0] = thetas
            colours[...,1] = deltas

        return colours

    def get_byte_values(self, channel_order, pixels):
        input_order = ["r", "g", "b"]
        pixel_order = [0,1,2]

        if "cylinder" in self.name:
            pixel_order = [1,0,2]
        input_values = np.array([np.take(pixels, pixel_order[0], axis=1),
                                 np.take(pixels, pixel_order[1], axis=1),
                                 np.take(pixels, pixel_order[2], axis=1)])

        if "w" in channel_order:
            w = np.min(pixels, axis=1)
            np.subtract(input_values, w)
            input_values = np.append(input_values, [w], axis=0)
            input_order.append("w")

        output_values = np.zeros(len(pixels) * len(channel_order), dtype=int)

        for index, cha in enumerate(channel_order):
            if cha not in input_order:
                raise Exception("Unknown colour channel ", cha)

            output_values[index::len(channel_order)] = input_values[input_order.index(cha)]

        np.clip(output_values, 0.0, 254.0)

        return output_values.astype(int)

    def power_limit(self, channel_order, byte_values):
        watts_per_rgb_bit = 0.00015  # watts per bit per rgb channel
        watts_per_w_bit = 0.00029  # watts per bit per w channel

        channel_total = np.sum(byte_values)

        if "w" in channel_order:
            w_total = np.sum(byte_values[channel_order.index("w")::len(channel_order)])
            rgb_total = channel_total - w_total

            total_draw = rgb_total * watts_per_rgb_bit + w_total * watts_per_w_bit

        else:
            total_draw = channel_total * watts_per_rgb_bit

        if total_draw > self.power_budget:
            downscale_factor = self.power_budget / total_draw

            byte_values *= downscale_factor

        return byte_values

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
        return name in list(sender_info.sender.name for sender_info in self.senders_info)
