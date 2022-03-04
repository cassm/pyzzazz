from handlers.controllers.controller_handler import ControllerHandler, Event
from handlers.connections.redis_handler import RedisHandler
import json


class RedisControllerHandler(ControllerHandler):
    def __init__(self):
        self.name = "REDIS_CONTROLLER"
        ControllerHandler.__init__(self, {"name": self.name})
        self.redis_client = RedisHandler.get_instance()

    # TODO this is bad
    def is_connected(self):
        return True

    def update(self):
        cmds = self.redis_client.lpop('pyzzazz:commands', 50)

        if not cmds:
            return

        for cmd in cmds:
            cmd_obj = json.loads(cmd)
            self._events.append(Event(
                target_keyword=cmd_obj["target_keyword"],
                command=cmd_obj["command"],
                value=cmd_obj["value"]
            ))
