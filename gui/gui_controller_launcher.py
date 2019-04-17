from gui.gui_controller import GuiController
from handlers.config_handler import ConfigHandler

# host = '192.168.1.102'
host = '127.0.0.1'



config_handler = ConfigHandler("conf/elephant_conf.json")
for controller_conf in config_handler.get_controllers():
    if controller_conf["type"] == "gui":
        gui_controller = GuiController(controller_conf, host)
        gui_controller.run()
        break
