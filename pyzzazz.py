from common.configparser import ConfigParser
from common.usb_serial_manager import UsbSerialManager
from senders.usb_serial_sender_handler import UsbSerialSenderHandler
from controllers.gui_controller_handler import GuiControllerHandler
from controllers.usb_serial_controller_handler import UsbSerialControllerHandler
from senders.opc_sender_handler import OpcSenderHandler
from common.palette_handler import PaletteHandler
from common.video_handler import VideoHandler
from common.socket_server import SocketServer
from fixtures.dodecahedron import Dodecahedron
from fixtures.cylinder import Cylinder
from fixtures.bunting import Bunting
from common.setting_handler import SettingHandler
from overlays.overlay_handler import OverlayHandler

import signal
import time
import re
import traceback
from pathlib import Path

start_pattern = "sparkle"
start_palette = "auto"
default_port = 48945

conf_file = "conf/elephant_conf.json"

class Pyzzazz:
    def __init__(self, conf_path, palette_path, video_path):
        self._src_dir = Path(__file__).parent
        self.config_parser = ConfigParser(conf_path)
        self.palette_handler = PaletteHandler(palette_path)
        self.video_handler = VideoHandler(video_path)
        self.usb_serial_manager = UsbSerialManager()
        self.effective_time = 0.0
        self.last_update = time.time()
        self.subprocesses = list()

        self.senders = []
        self.fixtures = []
        self.controllers = []

        self.setting_handlers = {}

        if self.needs_socket_server():
            self.socket_server = SocketServer(port=default_port)
        else:
            self.socket_server = None

        self.overlay_handler = OverlayHandler()

        # TODO multiple palettes, pass dict to fixtures
        # TODO add target type for commands (fixtures, master, etc)
        # TODO modulators? overlays?
        # TODO set from image/video
        # TODO video players should be a different type

        # these must be done in this order
        self.init_setting_handlers()
        self.init_senders()
        self.init_fixtures()
        self.init_controllers()
        self.register_commands()
        self.generate_opc_layout_files()

        # FIXME how to do startup command?
        for fixture in self.fixtures:
            command = {'type': 'pattern', 'name': start_pattern, 'args': {}}
            # command = {'type': 'pattern', 'name': 'make_me_one_with_everything', 'args': {}}
            fixture.register_command(command)
            fixture.receive_command(command, 1)

    def needs_socket_server(self):
        for controller_conf in self.config_parser.get_controllers():
            if controller_conf["type"] == "gui":
                return True

        return False

    def update(self):
        if self.socket_server:
            self.socket_server.poll()

        self.usb_serial_manager.update()

        smoothness = self.setting_handlers["master_settings"].get_value("smoothness", 0.5)
        brightness = self.setting_handlers["master_settings"].get_value("brightness", 1.0)
        speed = self.setting_handlers["master_settings"].get_value("speed", 0.5)

        self.palette_handler.set_master_palette_name(self.setting_handlers["master_settings"].get_value("palette", start_palette))
        self.palette_handler.set_space_per_palette(self.setting_handlers["master_settings"].get_value("space_per_palette", 0.5))
        self.palette_handler.set_time_per_palette(self.setting_handlers["master_settings"].get_value("time_per_palette", 0.5))

        self.video_handler.update(self.effective_time)

        self.effective_time += (time.time() - self.last_update) * speed * 3  # we want to go from 0 to triple speed
        self.last_update = time.time()

        for controller in self.controllers:
            if not controller.is_connected():
                controller.try_connect()

            if controller.is_connected():
                controller.update()

                events = controller.get_events()
                for event in events:
                    # FIXME this is hacky
                    if event.command["type"] == "overlay":
                        self.overlay_handler.receive_command(event.command, self.effective_time)

                    elif event.command["type"] == "video":
                        self.video_handler.receive_command(event.command)

                    else:
                        matching_fixtures = list(fixture for fixture in self.fixtures if re.search(event.target_regex, fixture.name))

                        for fixture in matching_fixtures:
                            fixture.receive_command(event.command, event.value)

                        matching_setts = list(sett for sett in self.setting_handlers.keys() if re.search(event.target_regex, sett))

                        for sett in matching_setts:
                            self.setting_handlers[sett].receive_command(event.command, event.value)

                controller.clear_events()

        for sender in self.senders:
            if not sender.is_connected():
                sender.try_connect()

        for fixture in self.fixtures:
            fixture.update(self.effective_time, self.palette_handler, smoothness, brightness)
            fixture.send()

        self.overlay_handler.update(self.effective_time)

    def init_senders(self):
        for sender_conf in self.config_parser.get_senders():
            # check for duplicate names
            self.sanity_check_sender_conf(sender_conf)

            if sender_conf.get("type", "") == "usb_serial":
                print("Creating usb serial sender handler {}".format(sender_conf.get("name", "")))
                self.senders.append(UsbSerialSenderHandler(sender_conf, self.usb_serial_manager))

            elif sender_conf.get("type", "") == "opc":
                print("Creating opc sender {} on port {}".format(sender_conf.get("name", ""), sender_conf.get("port", "")))
                self.senders.append(OpcSenderHandler(sender_conf, self._src_dir))

            else:
                raise Exception("Unknown sender type {}".format(sender_conf.get("type", "")))

        print("\n")

    def init_fixtures(self):
        # TODO create extra settings fixtures in the conf, specify them in led fixtures, and pass them in

        for fixture_conf in self.config_parser.get_fixtures():
            self.sanity_check_fixture_conf(fixture_conf)

            if fixture_conf.get("type", "") == "led":
                if fixture_conf.get("geometry", "") == "dodecahedron":
                    print("Creating dodecahedron {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    fixture_senders = list(sender for sender in self.senders if sender.name in fixture_conf.get("senders", []))
                    self.fixtures.append(Dodecahedron(fixture_conf, fixture_senders, self.overlay_handler, self.video_handler))

                elif fixture_conf.get("geometry", "") == "cylinder":
                    print("Creating cylinder {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    fixture_senders = list(sender for sender in self.senders if sender.name in fixture_conf.get("senders", []))
                    self.fixtures.append(Cylinder(fixture_conf, fixture_senders, self.overlay_handler, self.video_handler))

                elif fixture_conf.get("geometry", "") == "bunting":
                    print("Creating bunting {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    fixture_senders = list(sender for sender in self.senders if sender.name in fixture_conf.get("senders", []))
                    self.fixtures.append(Bunting(fixture_conf, fixture_senders, self.overlay_handler, self.video_handler))

                else:
                    raise Exception("Unknown fixture geometry {}".format(fixture_conf.get("geometry", "")))

            else:
                raise Exception("Unknown fixture type {}".format(fixture_conf.get("type", "")))

        print("\n")

    def init_controllers(self):
        for controller_conf in self.config_parser.get_controllers():
            # check for duplicate names
            self.sanity_check_controller_conf(controller_conf)

            if controller_conf.get("type", "") == "usb_serial":
                print("Creating usb serial controller {} on port {}".format(controller_conf.get("name", ""), controller_conf.get("port", "")))
                self.controllers.append(UsbSerialControllerHandler(controller_conf))

            elif controller_conf.get("type", "") == "gui":
                print("Creating gui controller {} on port {}".format(controller_conf.get("name", ""), controller_conf.get("port", "")))
                self.controllers.append(GuiControllerHandler(controller_conf, self.socket_server))

            else:
                raise Exception("Unknown controller type {}".format(controller_conf.get("type", "")))

        print("\n")

    def init_setting_handlers(self):
        # always create a master settings fixture
        self.setting_handlers["master_settings"] = SettingHandler("master_settings")

        # TODO add configurable ones here

    def register_commands(self):
        for controller in self.controllers:
            for control in controller.get_controls():
                # FIXME this is hacky also
                if control.command["type"] != "overlay":
                    matching_fixtures = list(fixture for fixture in self.fixtures if re.search(control.target_regex, fixture.name))

                    for fixture in matching_fixtures:
                        fixture.register_command(control.command)

                    matching_setts = list(sett for sett in self.setting_handlers.keys() if re.search(control.target_regex, sett))

                    for sett in matching_setts:
                        self.setting_handlers[sett].register_command(control.command, control.default)

    def generate_opc_layout_files(self):
        for sender in self.senders:
            if sender.type == "opc":
                sender.generate_layout_files(self.fixtures)
                opc_server_started = sender.start()

                if opc_server_started:
                    self.subprocesses.append(opc_server_started)

    def sanity_check_sender_conf(self, sender_conf):
        sender_names = tuple(sender.name for sender in self.senders)
        if sender_conf.get("name", "") in sender_names:
            raise Exception("Pyzzazz: config specifies one or more senders with identical name {}".format(sender_conf.get("name", "")))

        # check for duplicate ports
        # sender_ports = tuple(sender.port for sender in self.senders)
        # if sender_conf.get("port", "") in sender_ports:
        #     raise Exception("Pyzzazz: config specifies one or more senders with identical port {}".format(sender_conf.get("port", "")))

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

    def sanity_check_controller_conf(self, controller_conf):
        button_ids = list(button["id"] for button in controller_conf.get("buttons", []))
        if len(button_ids) != len(set(button_ids)):
            raise Exception("Pyzzazz: Controller {} specified with one or more duplicate button IDs".format(controller_conf.get("name", "")))

        slider_ids = list(slider["id"] for slider in controller_conf.get("sliders", []))
        if len(slider_ids) != len(set(slider_ids)):
            raise Exception("Pyzzazz: Controller {} specified with one or more duplicate slider IDs".format(controller_conf.get("name", "")))

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

    pyzzazz = None

    try:
        print("Initialising...")
        # FIXME backup last used conf
        # FIXME check for conf on usb stick
        # FIXME multiple palettes
        # FIXME grab palettes off usb stick
        pyzzazz = Pyzzazz(conf_file, "palettes/", "videos/")

        print("Running...")
        while True:
            pyzzazz.update()

            if killer.kill_now:
                if pyzzazz:
                    pyzzazz.shut_down()

                break

    except Exception as e:
        # FIXME output to file, print to screen if we're doing that?
        traceback.print_exc()

    finally:
        pyzzazz.shut_down()

    print("have a nice day :)")
