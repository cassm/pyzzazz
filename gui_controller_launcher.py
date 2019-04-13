from controllers.gui_controller import GuiController
from common.configparser import ConfigParser


config_parser = ConfigParser("conf/conf.json")
for controller_conf in config_parser.get_controllers():
    if controller_conf["type"] == "gui":
        gui_controller = GuiController(controller_conf)
        gui_controller.run()
        break
