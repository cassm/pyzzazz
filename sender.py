class Sender:
    def __init__(self, config):
        self.validate_config(config)

        self.name = config.get("name")
        self.type = config.get("type")
        self.num_lines = config.get("num_lines")

    def validate_config(self, config):
        if "name" not in config.keys():
            raise Exception("Sender: config contains no name")

        if "type" not in config.keys():
            raise Exception("Sender: config contains no type")

        if "num_lines" not in config.keys():
            raise Exception("Sender: config contains no num_lines")

    def is_connected(self):
        pass

    def try_connect(self):
        pass

    def send(self, line, pixels):
        pass
