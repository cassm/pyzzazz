import json
import os


class CalibrationHandler:
    def __init__(self, conf_path):
        self.conf_path = os.path.join(os.getcwd(), conf_path)

        if os.path.isfile(self.conf_path):
            with open(self.conf_path) as file:
                try:
                    self.config = json.load(file)

                except json.JSONDecodeError:
                    raise Exception("CalibrationParser: File not valid JSON")

        else:
            self.config = dict()
            self.save_conf()

        self.calibration_changed = True
        self.current_selection = 0

    def register_fixture(self, fixture):
        if fixture not in self.config.keys():
            self.config[fixture] = 0

    def get_angle(self, fixture):
        return self.config.get(fixture, 0)

    def set_angle(self, fixture, angle):
        self.config[fixture] = angle
        self.save_conf()

    def add_angle_to_selection(self, angle):
        self.config[self.get_selection()] += angle
        self.save_conf()

    def increment_selection(self):
        self.current_selection += 1
        self.current_selection %= len(self.config.keys())

    def get_selection(self):
        selection = list(self.config.keys())[self.current_selection]
        return selection

    def save_conf(self):
        with open(self.conf_path, 'w') as outfile:
            json.dump(self.config, outfile)
