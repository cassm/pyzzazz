from handlers.connections.redis_handler import RedisHandler
import json
import os

class NodeConfigHandler:
    def __init__ (self, conf_path):
        self.conf_path = conf_path
        self.redis_client = RedisHandler.get_instance()

        if os.path.isfile(self.conf_path):
            with open(self.conf_path) as file:
                try:
                    self.config = json.load(file)
                    self.push_config()

                except json.JSONDecodeError:
                    raise Exception("NodeConfigHandler: File not valid JSON")

        else:
            self.config = dict()
            self.save_conf()

    def push_config(self):
        for key, value in self.config.get("fixtures", {}).items():
            RedisHandler.try_command(self.redis_client.hset, "pyzzazz:clients", key, value)

        for key, value in self.config.get("colour_modes", {}).items():
            RedisHandler.try_command(self.redis_client.hset, "pyzzazz:colourModes", key, value)

    def pull_config(self):
        config_changed = False

        new_fixture_config = RedisHandler.try_command(self.redis_client.hgetall, "pyzzazz:clients")
        if new_fixture_config:
            if "fixtures" not in self.config.keys():
                self.config["fixtures"] = {}
                config_changed = True

            for key, value in new_fixture_config.items():
                oldVal = self.config["fixtures"].get(key, "uninitialised") 
                if oldVal!= value:
                    print(f"NodeConfigHandler: fixtures:{key} {oldVal} -> {value}")
                    self.config["fixtures"][key] = value
                    config_changed = True

        new_colour_mode_config = RedisHandler.try_command(self.redis_client.hgetall, "pyzzazz:colourModes")
        if new_colour_mode_config:
            if "colour_modes" not in self.config.keys():
                self.config["colour_modes"] = {}
                config_changed = True

            for key, value in new_colour_mode_config.items():
                oldVal = self.config["colour_modes"].get(key, "")
                if oldVal != value:
                    print(f"NodeConfigHandler: fixtures:{key} {oldVal} -> {value}")
                    self.config["colour_modes"][key] = value
                    config_changed = True

        if config_changed:
            self.save_conf()


    def save_conf(self):
        with open(self.conf_path, 'w') as outfile:
            json.dump(self.config, outfile)
