import json
import os


class ConfigHandler:
    def __init__(self, conf_path):
        conf_path = os.path.join(os.getcwd(), conf_path)

        try:
            with open(conf_path) as file:
                try:
                    self.config = json.load(file)

                except json.JSONDecodeError:
                    raise Exception("ConfigParser: File not valid JSON")

        except EnvironmentError:
            raise Exception("ConfigParser: File does not exist")

    def get_fixtures(self):
        return self.config.get("Fixtures", [])

    def get_controllers(self):
        return self.config.get("Controllers", [])

    def get_senders(self):
        return self.config.get("Senders", [])
