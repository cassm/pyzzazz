from configparser import ConfigParser
from sender import Sender
from palette import Palette
from dodecahedron import Dodecahedron
import signal
import time


class Pyzzazz:
    def __init__(self, conf_path, palette_path):
        self.config_parser = ConfigParser(conf_path)
        self.palette = Palette(palette_path)
        self.speed = 1.0
        self.effective_time = 0.0
        self.last_update = time.time()

        senders = self.config_parser.get_senders()
        controllers = self.config_parser.get_controllers()

        self.senders = []
        for sender_conf in self.config_parser.get_senders():
            # check for duplicate names
            sender_names = tuple(sender.name for sender in self.senders)
            if sender_conf.get("name", "") in sender_names:
                raise Exception("Pyzzazz: config specifies one or more senders with identical name {}".format(sender_conf.get("name", "")))

            # check for duplicate ports
            sender_ports = tuple(sender.port for sender in self.senders)
            if sender_conf.get("port", "") in sender_ports:
                raise Exception("Pyzzazz: config specifies one or more senders with identical port {}".format(sender_conf.get("port", "")))

            print("Creating sender {} on port {}".format(sender_conf.get("name", ""), sender_conf.get("port", "")))
            self.senders.append(Sender(sender_conf))

        self.fixtures = []
        for fixture_conf in self.config_parser.get_fixtures():
            # check for duplicate names
            fixture_names = tuple(fixture.name for fixture in self.fixtures)
            if fixture_conf.get("name", "") in fixture_names:
                raise Exception("Pyzzazz: config specifies one or more fixtures with identical name {}".format(fixture_conf.get("name", "")))

            # check sender exists
            sender_names = tuple(sender.name for sender in self.senders)
            sender_name = fixture_conf.get("sender", "")
            if sender_name not in sender_names:
                raise Exception("Pyzzazz: Fixture {} specified with undefined sender {}".format(fixture_conf.get("name", ""), sender_name))

            if fixture_conf.get("geometry", "") == "dodecahedron":
                print("Creating dodecahedron {} with sender {}".format(fixture_conf.get("name", ""), fixture_conf.get("sender", "")))
                self.fixtures.append(Dodecahedron(fixture_conf, self.senders[sender_names.index(sender_name)]))
                break

    def update(self):
        self.effective_time += (time.time() - self.last_update) * self.speed

        for sender in self.senders:
            if not sender.is_connected():
                sender.try_connect()


        for fixture in self.fixtures:
            fixture.update(self.effective_time)
            fixture.send()


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
