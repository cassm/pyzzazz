from fixture import Fixture


class LedFixture(Fixture):
    def __init__(self, config, sender):
        Fixture.__init__(self, config, sender)
        self.geometry = config.get("geometry", "No geometry present in fixture definition")
        self.num_pixels = config.get("num_pixels", "No num_pixels present in fixture definition")

        self.buffer = [[0.0, 0.0, 0.0]] * self.num_pixels

    def send(self):
        self.sender.send(self.line, self.buffer)
