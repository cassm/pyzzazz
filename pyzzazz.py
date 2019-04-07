from configparser import ConfigParser
from palette import Palette


class Pyzzazz:
    def __init__(self, conf_path, palette_path):
        self.config_parser = ConfigParser(conf_path)
        self.palette = Palette(palette_path)

        fixtures = self.config_parser.get_fixtures()
        senders = self.config_parser.get_senders()
        controllers = self.config_parser.get_controllers()


def main():
    pyzzazz = Pyzzazz("conf/conf.json", "conf/auto.bmp")


if __name__ == "__main__":
    main()
