import json
import os


class ConfigParser:
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
        try:
            return self.config["Fixtures"]
        except KeyError:
            raise Exception("ConfigParser: config contains no fixtures")

    def get_controllers(self):
        try:
            return self.config["Controllers"]
        except KeyError:
            raise Exception("ConfigParser: config contains no controllers")

    def get_senders(self):
        try:
            return self.config["Senders"]
        except KeyError:
            raise Exception("ConfigParser: config contains no senders")
