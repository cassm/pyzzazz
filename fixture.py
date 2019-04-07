class Fixture:
    def __init__(self, config, sender):
        self.name = config.get("name", "No name present in fixture definition")
        self.location = config.get("location", "No location present in fixture definition")
        self.line = config.get("line", "No line present in fixture definition")
        self.sender = sender

    def send(self):
        pass

    def receive_command(self, command_string):
        pass

    def refresh(self):
        pass
