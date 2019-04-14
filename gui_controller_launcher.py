from controllers.gui_controller import GuiController
from common.configparser import ConfigParser

# host = '192.168.1.102'
host = '127.0.0.1'

config_parser = ConfigParser("conf/conf.json")
for controller_conf in config_parser.get_controllers():
    if controller_conf["type"] == "gui":
        gui_controller = GuiController(controller_conf, host)
        gui_controller.run()
        break
