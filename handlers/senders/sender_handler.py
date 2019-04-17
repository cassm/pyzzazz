class SenderHandler:
    def __init__(self, config):
        self.validate_config(config)

        self.name = config.get("name")
        self.type = config.get("type")
        self.is_simulator = config.get("is_simulator", False)

    def validate_config(self, config):
        if "name" not in config.keys():
            raise Exception("Sender: config contains no name")

        if "type" not in config.keys():
            raise Exception("Sender: config contains no type")

    def is_connected(self):
        pass

    def try_connect(self):
        pass

    def send(self, line, byte_values):
        pass
