from configparser import ConfigParser
from palette import Palette
from dodecahedron import Dodecahedron


class Pyzzazz:
    def __init__(self, conf_path, palette_path):
        self.config_parser = ConfigParser(conf_path)
        self.palette = Palette(palette_path)

        senders = self.config_parser.get_senders()
        controllers = self.config_parser.get_controllers()

        self.fixtures = []
        for fixture in self.config_parser.get_fixtures():
            if fixture.get("geometry", "") == "dodecahedron":
                # FIXME pass in sender here
                self.fixtures.append(Dodecahedron(fixture, None))


def main():
    pyzzazz = Pyzzazz("conf/conf.json", "conf/auto.bmp")


if __name__ == "__main__":
    main()
