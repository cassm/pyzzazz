from handlers.config_handler import ConfigHandler
from handlers.connections.usb_serial_handler import UsbSerialHandler
from handlers.senders.usb_serial_sender_handler import UsbSerialSenderHandler
from handlers.controllers.gui_controller_handler import GuiControllerHandler
from handlers.controllers.usb_serial_controller_handler import UsbSerialControllerHandler
from handlers.senders.opc_sender_handler import OpcSenderHandler
from handlers.palette_handler import PaletteHandler
from handlers.video_handler import VideoHandler
from handlers.connections.socket_server import SocketServer
from handlers.connections.udp_handler import UdpHandler
from handlers.senders.udp_sender_handler import UdpSenderHandler
from handlers.external_drive_handler import ExternalDriveHandler
from fixtures.dodecahedron import Dodecahedron
from fixtures.cylinder import Cylinder
from fixtures.bunting_polygon import BuntingPolygon
from fixtures.arch import Arch
from handlers.setting_handler import SettingHandler
from handlers.calibration_handler import CalibrationHandler
from handlers.hotkey_handler import HotKeyHandler
from overlays.overlay_handler import OverlayHandler
from common.graceful_killer import GracefulKiller

import time
import traceback
from pathlib import Path
import sys
import tty
import termios
from shutil import copyfile

# TODO fixture groups

start_pattern = "smooth"
start_palette = "jellyfish"
default_tcp_port = 48945
default_udp_port = 2390

conf_file = "conf/elephant_conf.json"
calibration_file = "conf/calibration.json"

class Pyzzazz:
    def __init__(self, conf_path, palette_path, video_path, calibration_path):
        self._src_dir = Path(__file__).parent

        self.external_drive_handler = ExternalDriveHandler()

        if len(self.external_drive_handler.get_config_paths()) > 0:
            copyfile(self.external_drive_handler.get_config_paths()[0], conf_path)

        if len(self.external_drive_handler.get_calibration_paths()) > 0:
            copyfile(self.external_drive_handler.get_calibration_paths()[0], conf_path)

        for path in self.external_drive_handler.get_palette_paths():
            copyfile(path, palette_path)

        for path in self.external_drive_handler.get_video_paths():
            copyfile(path, video_path)

        self.config_parser = ConfigHandler(conf_path)
        self.palette_handler = PaletteHandler(palette_path)
        self.calibration_handler = CalibrationHandler(calibration_path)

        self.video_handlers = dict()

        self.video_handlers["led_fix_icosahedron"] = VideoHandler(video_path)
        self.video_handlers["led_fix_cylinder"] = VideoHandler(video_path)
        self.video_handlers["led_fix_bunting"] = VideoHandler(video_path)

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
            self.socket_server = SocketServer(port=default_tcp_port)
        else:
            self.socket_server = None

        self.udp_handler = UdpHandler(default_udp_port)

        self.overlay_handler = OverlayHandler()

        # these must be done in this order
        self.init_setting_handlers()
        self.init_senders()
        self.init_fixtures()
        self.init_controllers()
        self.register_commands()
        self.generate_opc_layout_files()

        self.hotkey_handler = HotKeyHandler(self.fixtures, self.calibration_handler)

        self.update_video = self.video_used()

    def video_used(self):
        for controller_conf in self.config_parser.get_controllers():
            for button in controller_conf["buttons"]:
                if button["command"]["name"] == "map_video":
                    return True

        return False

    def needs_socket_server(self):
        for controller_conf in self.config_parser.get_controllers():
            if controller_conf["type"] == "gui":
                return True

        return False

    def update(self):
        if self.socket_server:
            self.socket_server.poll()

        self.udp_handler.poll()

        self.hotkey_handler.poll()

        self.usb_serial_manager.update()

        smoothness = self.setting_handlers["master_settings"].get_value("smoothness", 0.5)
        brightness = self.setting_handlers["master_settings"].get_value("brightness", 0.5)
        speed = self.setting_handlers["master_settings"].get_value("speed", 0.5)

        self.palette_handler.set_master_palette_name(self.setting_handlers["master_settings"].get_value("palette", start_palette))
        self.palette_handler.set_palette_space_factor(self.setting_handlers["master_settings"].get_value("space_per_palette", 0.5))
        self.palette_handler.set_palette_time_factor(self.setting_handlers["master_settings"].get_value("time_per_palette", 0.5))

        if self.update_video:
            for video_handler in self.video_handlers.values():
                video_handler.set_scaling_factor(self.setting_handlers["master_settings"].get_value("space_per_palette", 0.5) / 2 + 0.5)

        for controller in self.controllers:
            if not controller.is_connected():
                controller.try_connect()

            if controller.is_connected():
                controller.update()

                events = controller.get_events()
                for event in events:
                    if event.is_overlay():
                        self.overlay_handler.receive_command(event.command)

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

        # prevent senders and video updating too often
        if self.last_update + self.time_per_frame > time.time():
            return

        self.effective_time += (time.time() - self.last_update) * speed * 3  # we want to go from 0 to triple speed
        self.last_update = time.time()


        for sender in self.senders.values():
            if not sender.is_connected():
                sender.try_connect()

        if self.update_video:
            for video_handler in self.video_handlers.values():
                video_handler.update(self.effective_time)

        for fixture in self.fixtures:
            fixture.update(self.effective_time, self.palette_handler, smoothness, brightness)
            fixture.send()
            self.usb_serial_manager.update()

        self.overlay_handler.update()

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

            elif sender_conf.get("type", "") == "udp":
                print("Creating UDP sender {}".format(name))
                self.senders[name] = UdpSenderHandler(sender_conf, self.udp_handler)

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
                    self.fixtures.append(Dodecahedron(fixture_conf, fixture_senders, self.overlay_handler, self.video_handlers["led_fix_icosahedron"], self.calibration_handler))

                elif fixture_conf.get("geometry", "") == "cylinder":
                    print("Creating cylinder {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    self.fixtures.append(Cylinder(fixture_conf, fixture_senders, self.overlay_handler, self.video_handlers["led_fix_cylinder"], self.calibration_handler))

                elif fixture_conf.get("geometry", "") == "bunting_polygon":
                    print("Creating bunting polygon {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    self.fixtures.append(BuntingPolygon(fixture_conf, fixture_senders, self.overlay_handler, self.video_handlers["led_fix_bunting"], self.calibration_handler))

                elif fixture_conf.get("geometry", "") == "arch":
                    print("Creating arch {} with senders {}".format(fixture_conf.get("name", ""), fixture_conf.get("senders", [])))
                    self.fixtures.append(Arch(fixture_conf, fixture_senders, self.overlay_handler, self.video_handlers["led_fix_bunting"], self.calibration_handler))

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
                self.controllers.append(UsbSerialControllerHandler(controller_conf, self.usb_serial_manager))

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
    term_saved = False
    old_settings = None

    try:
        old_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        term_saved = True
    except:
        pass

    killer = GracefulKiller()

    pyzzazz = None

    try:
        print("Initialising...")
        # FIXME backup last used conf
        # FIXME check for conf on usb stick
        # FIXME grab palettes off usb stick
        # FIXME grab videos off usb stick
        pyzzazz = Pyzzazz(conf_file, "palettes/", "videos/", calibration_file)

        print("Running...")
        while True:
            pyzzazz.update()

            if killer.kill_now or pyzzazz.hotkey_handler.exit:
                if term_saved:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

                if pyzzazz:
                    pyzzazz.shut_down()

                break

    except Exception as e:
        # FIXME output to file, print to screen if we're doing that?
        traceback.print_exc()

    finally:
        if term_saved:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        pyzzazz.shut_down()

    print("have a nice day :)")
