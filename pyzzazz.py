from configparser import ConfigParser
from palette import Palette
from dodecahedron import Dodecahedron
import signal


class Pyzzazz:
    def __init__(self, conf_path, palette_path):
        self.config_parser = ConfigParser(conf_path)
        self.palette = Palette(palette_path)
        self.speed = 1.0
        self.effective_time = 0.0
        self.last_update = time.time()

        senders = self.config_parser.get_senders()
        controllers = self.config_parser.get_controllers()

        self.fixtures = []
        for fixture in self.config_parser.get_fixtures():
            if fixture.get("geometry", "") == "dodecahedron":
                # FIXME pass in sender here
                self.fixtures.append(Dodecahedron(fixture, None))

class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        print("SIGKILL received")
        self.kill_now = True


if __name__ == "__main__":
    killer = GracefulKiller()

    print("Initialising...")
    pyzzazz = Pyzzazz("conf/conf.json", "conf/auto.bmp")

    print("Running...")
    while True:
        pyzzazz.update()

        if killer.kill_now:
            break

    print("have a nice day :)")
