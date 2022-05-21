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
        cmdLists = RedisHandler.try_command(self.redis_client.lpop, 'pyzzazz:commands', 50)

        if not cmdLists:
            return

        for cmds in cmdLists:
            cmds_obj = json.loads(cmds)
            for cmd in cmds_obj:
                self._events.append(Event(
                    target_keyword=cmd["target_keyword"],
                    command=cmd["command"],
                    value=cmd["value"]
                ))
