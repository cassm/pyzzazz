class Fixture:
    def __init__(self, config, overlay_handler, video_handler, calibration_handler):
        self.validate_config(config)

        self.name = config.get("name")
        self.location = config.get("location")
        self.palette_name = None
        self.overlay_handler = overlay_handler
        self.video_handler = video_handler
        self.calibration_handler = calibration_handler
        self.calibration_angle = 0
        self.calibrate = False

        self.calibration_handler.register_fixture(self.name)

    def validate_config(self, config):
        if "name" not in config.keys():
            raise Exception("Fixture: config contains no name")

        if "location" not in config.keys():
            raise Exception("Fixture: config contains no location")

        if "sender" not in config.keys():
            raise Exception("Fixture: config contains no sender")

    def toggle_calibrate(self):
        pass

    def send(self):
        pass

    def register_command(self, command):
        pass

    def receive_command(self, command, value):
        pass

    def update(self, time, palette, smoothness, master_brightness):
        pass
