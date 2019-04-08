class Fixture:
    def __init__(self, config):
        self.name = config.get("name", "No name present in fixture definition")
        self.location = config.get("location", "No location present in fixture definition")

    def send(self):
        pass

    def parse_command(self, command_string):
        pass

    def refresh(self):
        pass
