from handlers.controllers.controller_handler import ControllerHandler, Event
from handlers.connections.redis_handler import RedisHandler
import json


class RedisControllerHandler(ControllerHandler):
    def __init__(self, calibration_handler, fixtures):
        self.name = "REDIS_CONTROLLER"
        ControllerHandler.__init__(self, {"name": self.name})
        self.calibration_handler = calibration_handler
        self.fixtures = fixtures
        self.redis_client = RedisHandler.get_instance()

    # TODO this is bad
    def is_connected(self):
        return True

    def update(self):
        cmdLists = RedisHandler.try_command(self.redis_client.lpop, 'pyzzazz:commands', 50)

        if not cmdLists:
            return

        for cmds in cmdLists:
            cmds_obj = json.loads(cmds)
            print(cmds_obj)
            for cmd in cmds_obj:
                if cmd["command"]["type"] == "calibration":
                    self.calibration_handler.add_angle_to_fixture(
                            cmd["target_keyword"],
                            cmd["value"])

                elif cmd["command"]["type"] == "toggle_calibration":
                    for fixture in self.fixtures:
                        fixture.toggle_calibrate()

                else:
                    self._events.append(Event(
                        target_keyword=cmd["target_keyword"],
                        command=cmd["command"],
                        value=cmd["value"]
                    ))
