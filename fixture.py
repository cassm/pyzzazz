class Fixture:
    def __init__(self, config):
        self.validate_config(config)

        self.name = config.get("name")
        self.location = config.get("location")

    def validate_config(self, config):
        if "name" not in config.keys():
            raise Exception("Fixture: config contains no name")

        if "location" not in config.keys():
            raise Exception("Fixture: config contains no location")

        if "sender" not in config.keys():
            raise Exception("Fixture: config contains no sender")

    def send(self):
        pass

    def parse_command(self, command_string):
        pass

    def refresh(self):
        pass
