from configparser import ConfigParser
from usb_serial_sender import UsbSerialSender
from opc_sender import OpcSender
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
        self.subprocesses = []

        # TODO multiple palettes, pass dict to fixtures
        #      controllers
        #      add target type for commands (fixtures, master, etc)
        #      modulators? overlays?
        #      set from image/video

        controllers = self.config_parser.get_controllers()

        self.senders = []
        for sender_conf in self.config_parser.get_senders():
            # check for duplicate names
            self.sanity_check_sender_conf(sender_conf)

            if sender_conf.get("type", "") == "usb_serial":
                print("Creating usb serial sender {} on port {}".format(sender_conf.get("name", ""), sender_conf.get("port", "")))
                self.senders.append(UsbSerialSender(sender_conf))

            elif sender_conf.get("type", "") == "opc":
                print("Creating opc sender {} on port {}".format(sender_conf.get("name", ""), sender_conf.get("port", "")))
                self.senders.append(OpcSender(sender_conf))

        print("\n")

        self.fixtures = []
        for fixture_conf in self.config_parser.get_fixtures():
            self.sanity_check_fixture_conf(fixture_conf)

            if fixture_conf.get("geometry", "") == "dodecahedron":
                print("Creating dodecahedron {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                fixture_senders = list(sender for sender in self.senders if sender.name in fixture_conf.get("senders", []))
                self.fixtures.append(Dodecahedron(fixture_conf, fixture_senders))

        print("\n")

        for sender in self.senders:
            if sender.type == "opc":
                sender.generate_layout_files(self.fixtures)
                self.subprocesses.append(sender.start())

        #FIXME do controllers here
        print ("{} fixtures initialised".format(len(self.fixtures)))
        for fixture in self.fixtures:
            print("{} with {} leds".format(fixture.name, len(fixture.leds)))
            fixture.register_command("pattern sparkle")
            fixture.parse_command("pattern sparkle")

    def sanity_check_sender_conf(self, sender_conf):
        sender_names = tuple(sender.name for sender in self.senders)
        if sender_conf.get("name", "") in sender_names:
            raise Exception("Pyzzazz: config specifies one or more senders with identical name {}".format(sender_conf.get("name", "")))

        # check for duplicate ports
        sender_ports = tuple(sender.port for sender in self.senders)
        if sender_conf.get("port", "") in sender_ports:
            raise Exception("Pyzzazz: config specifies one or more senders with identical port {}".format(sender_conf.get("port", "")))

    def sanity_check_fixture_conf(self, fixture_conf):
        # check for duplicate names
        for fixture in self.fixtures:
            if fixture_conf.get("name", "") == fixture.name:
                raise Exception("Pyzzazz: config specifies one or more fixtures with identical name {}".format(fixture_conf.get("name", "")))

            for sender_name in fixture_conf.get("senders", []):
                if fixture.has_sender(sender_name) and fixture_conf.get("line", "") == fixture.line:
                    raise Exception("Pyzzazz: config specifies one or more fixtures with identical senders {} and lines {}".format(sender_name, fixture_conf.get("line", "")))

        # check sender exists
        for sender_name in fixture_conf.get("senders", []):
            if sender_name not in list(sender.name for sender in self.senders):
                raise Exception("Pyzzazz: Fixture {} specified with undefined sender {}".format(fixture_conf.get("name", ""), sender_name))


    def update(self):
        self.effective_time += (time.time() - self.last_update) * self.speed
        self.last_update = time.time()

        for sender in self.senders:
            if not sender.is_connected():
                sender.try_connect()

        for fixture in self.fixtures:
            fixture.update(self.effective_time, self.palette)
            fixture.send()

    def shut_down(self):
        print("Shutting down...")
        for p in self.subprocesses:
            p.kill()


class GracefulKiller:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
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
            pyzzazz.shut_down()
            break

    print("have a nice day :)")
