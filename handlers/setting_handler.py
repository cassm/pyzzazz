class SettingHandler:
    def __init__(self, name):
        self.name = name
        self.settings = dict()

    def register_command(self, command, default=None):
        if command["type"] == "slider":
            if command["name"] not in self.settings.keys():
                # start everything in the middle
                self.settings[command["name"]] = default
                print("SettingHandler {} registering slider {} with default {}".format(self.name, command["name"], default))

        # FIXME how to verify these are present?
        elif command["type"] == "palette":
            # this is handled but no actions are necessary
            pass

        else:
            raise Exception("MasterSettingsFixture: unhandled command type {}".format(command["type"]))

    def receive_command(self, command, value):
        # if command["name"] not in self.settings.keys():
        #     raise Exception("MasterSettingsFixture: unregistered command {}".format(command["name"]))

        if command["type"] == "slider":
            # sliders are 0 - 1024 and we want them as 0 - 1
            self.settings[command["name"]] = float(value) / 1024.0

        elif command["type"] == "palette":
            self.settings["palette"] = command["name"]

        else:
            self.settings[command["name"]] = value

    def get_value(self, setting_name, default):
        if setting_name in self.settings.keys():
            return self.settings[setting_name]
        else:
            return default
