from handlers.config_handler import ConfigHandler
from handlers.usb_serial_handler import UsbSerialHandler
from handlers.senders.usb_serial_sender_handler import UsbSerialSenderHandler
from handlers.controllers.gui_controller_handler import GuiControllerHandler
from handlers.controllers.usb_serial_controller_handler import UsbSerialControllerHandler
from handlers.senders.opc_sender_handler import OpcSenderHandler
from handlers.palette_handler import PaletteHandler
from handlers.video_handler import VideoHandler
from common.socket_server import SocketServer
from fixtures.dodecahedron import Dodecahedron
from fixtures.cylinder import Cylinder
from fixtures.bunting_polygon import BuntingPolygon
from handlers.setting_handler import SettingHandler
from overlays.overlay_handler import OverlayHandler
from common.graceful_killer import GracefulKiller

import time
import traceback
from pathlib import Path

# TODO fixture groups

start_pattern = "sparkle"
start_palette = "auto"
default_port = 48945

conf_file = "conf/elephant_conf.json"

class Pyzzazz:
    def __init__(self, conf_path, palette_path, video_path):
        self._src_dir = Path(__file__).parent
        self.config_parser = ConfigHandler(conf_path)
        self.palette_handler = PaletteHandler(palette_path)

        self.video_handlers = dict()

        self.video_handlers["icosahedron"] = VideoHandler(video_path)
        self.video_handlers["cylinder"] = VideoHandler(video_path)
        self.video_handlers["bunting"] = VideoHandler(video_path)

        self.usb_serial_manager = UsbSerialHandler()
        self.effective_time = 0.0
        self.last_update = time.time()
        self.subprocesses = list()

        self.fps = 30.0
        self.time_per_frame = 1.0 / self.fps

        self.senders = dict()
        self.fixtures = []
        self.controllers = []

        self.setting_handlers = {}

        if self.needs_socket_server():
            self.socket_server = SocketServer(port=default_port)
        else:
            self.socket_server = None

        self.overlay_handler = OverlayHandler()

        # these must be done in this order
        self.init_setting_handlers()
        self.init_senders()
        self.init_fixtures()
        self.init_controllers()
        self.register_commands()
        self.generate_opc_layout_files()

    def needs_socket_server(self):
        for controller_conf in self.config_parser.get_controllers():
            if controller_conf["type"] == "gui":
                return True

        return False

    def update(self):
        if self.socket_server:
            self.socket_server.poll()

        self.usb_serial_manager.update()

        if self.last_update + self.time_per_frame > time.time():
            return

        smoothness = self.setting_handlers["master_settings"].get_value("smoothness", 0.5)
        brightness = self.setting_handlers["master_settings"].get_value("brightness", 1.0)
        speed = self.setting_handlers["master_settings"].get_value("speed", 0.5)

        self.effective_time += (time.time() - self.last_update) * speed * 3  # we want to go from 0 to triple speed
        self.last_update = time.time()

        self.palette_handler.set_master_palette_name(self.setting_handlers["master_settings"].get_value("palette", start_palette))
        self.palette_handler.set_space_per_palette(self.setting_handlers["master_settings"].get_value("space_per_palette", 0.5))
        self.palette_handler.set_time_per_palette(self.setting_handlers["master_settings"].get_value("time_per_palette", 0.5))

        for controller in self.controllers:
            if not controller.is_connected():
                controller.try_connect()

            if controller.is_connected():
                controller.update()

                events = controller.get_events()
                for event in events:
                    if event.is_overlay():
                        self.overlay_handler.receive_command(event.command, self.effective_time)

                    else:
                        if event.is_video():
                            matching_vid_handlers = list(handler_name for handler_name in self.video_handlers.keys()
                                                         if event.target_keyword in handler_name)

                            for handler_name in matching_vid_handlers:
                                self.video_handlers[handler_name].receive_command(event.command)

                        matching_fixtures = list(fixture for fixture in self.fixtures
                                                 if event.target_keyword in fixture.name)

                        for fixture in matching_fixtures:
                            fixture.receive_command(event.command, event.value)

                        matching_setts = list(sett for sett in self.setting_handlers.keys()
                                              if event.target_keyword in sett)

                        for sett in matching_setts:
                            self.setting_handlers[sett].receive_command(event.command, event.value)

                controller.clear_events()

        for sender in self.senders.values():
            if not sender.is_connected():
                sender.try_connect()

        for video_handler in self.video_handlers.values():
            video_handler.update(self.effective_time)

        for fixture in self.fixtures:
            fixture.update(self.effective_time, self.palette_handler, smoothness, brightness)
            fixture.send()

        self.overlay_handler.update(self.effective_time)

    def init_senders(self):
        for sender_conf in self.config_parser.get_senders():
            # check for duplicate names
            self.sanity_check_sender_conf(sender_conf)

            name = sender_conf.get("name")

            if sender_conf.get("type", "") == "usb_serial":
                print("Creating usb serial sender handler {}".format(name))
                self.senders[name] = UsbSerialSenderHandler(sender_conf, self.usb_serial_manager)

            elif sender_conf.get("type", "") == "opc":
                print("Creating opc sender {} on port {}".format(name, sender_conf.get("port", "")))
                self.senders[name] = OpcSenderHandler(sender_conf, self._src_dir)

            else:
                raise Exception("Unknown sender type {}".format(sender_conf.get("type", "")))

        print("\n")

    def init_fixtures(self):
        # TODO create extra settings fixtures in the conf, specify them in led fixtures, and pass them in

        for fixture_conf in self.config_parser.get_fixtures():
            self.sanity_check_fixture_conf(fixture_conf)

            if fixture_conf.get("type", "") == "led":
                fixture_senders = list()
                for sender_info in fixture_conf.get("senders", []):
                    fixture_senders.append((self.senders[sender_info[0]], sender_info[1]))

                if fixture_conf.get("geometry", "") == "dodecahedron":
                    print("Creating dodecahedron {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    self.fixtures.append(Dodecahedron(fixture_conf, fixture_senders, self.overlay_handler, self.video_handlers["icosahedron"]))

                elif fixture_conf.get("geometry", "") == "cylinder":
                    print("Creating cylinder {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    self.fixtures.append(Cylinder(fixture_conf, fixture_senders, self.overlay_handler, self.video_handlers["cylinder"]))

                elif fixture_conf.get("geometry", "") == "bunting_polygon":
                    print("Creating bunting polygon {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    self.fixtures.append(BuntingPolygon(fixture_conf, fixture_senders, self.overlay_handler, self.video_handlers["bunting"]))

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
                print("Creating usb serial controllers {} on port {}".format(controller_conf.get("name", ""), controller_conf.get("port", "")))
                self.controllers.append(UsbSerialControllerHandler(controller_conf))

            elif controller_conf.get("type", "") == "gui":
                print("Creating gui controllers {} on port {}".format(controller_conf.get("name", ""), controller_conf.get("port", "")))
                self.controllers.append(GuiControllerHandler(controller_conf, self.socket_server))

            else:
                raise Exception("Unknown controllers type {}".format(controller_conf.get("type", "")))

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
                    matching_fixtures = list(fixture for fixture in self.fixtures if control.target_keyword in fixture.name)

                    for fixture in matching_fixtures:
                        fixture.register_command(control.command)

                    matching_setts = list(sett for sett in self.setting_handlers.keys() if control.target_keyword in sett)

                    for sett in matching_setts:
                        self.setting_handlers[sett].register_command(control.command, control.default)

    def generate_opc_layout_files(self):
        for sender in self.senders.values():
            if sender.type == "opc":
                sender.generate_layout_files(self.fixtures)
                opc_server_started = sender.start()

                if opc_server_started:
                    self.subprocesses.append(opc_server_started)

    def sanity_check_sender_conf(self, sender_conf):
        sender_names = tuple(self.senders.keys())
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

            for new_sender_info in fixture_conf.get("senders", []):
                for existing_sender_info in fixture.senders_info:
                    if new_sender_info[0] == existing_sender_info.sender.name and new_sender_info[1] == existing_sender_info.line:
                        raise Exception("Pyzzazz: config specifies one or more fixtures with identical senders {} and lines {}".format(new_sender_info[0], new_sender_info[1]))

        # check sender exists
        for sender_info in fixture_conf.get("senders", []):
            if sender_info[0] not in list(sender.name for sender in self.senders.values()):
                raise Exception("Pyzzazz: Fixture {} specified with undefined sender {}".format(fixture_conf.get("name", ""), sender_info[0]))

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


if __name__ == "__main__":
    killer = GracefulKiller()

    pyzzazz = None

    try:
        print("Initialising...")
        # FIXME backup last used conf
        # FIXME check for conf on usb stick
        # FIXME grab palettes off usb stick
        # FIXME grab videos off usb stick
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
