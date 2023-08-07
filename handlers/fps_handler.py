import json
import os

class FpsHandler():
    def __init__(self, fps, conf_path):
        self.conf_path = conf_path
        self.fps = 0
        self.frame_interval = 0

        if os.path.isfile(self.conf_path):
            with open(self.conf_path) as file:
                try:
                    fps = json.load(file)["fps"]
                except json.JSONDecodeError:
                    raise Exception("FpsHandler: File not valid JSON")

        self.set_fps(fps)

    def set_fps(self, fps):
        self.fps = fps
        self.frame_interval = 1.0/fps
        with open(self.conf_path, 'w') as outfile:
            json.dump({"fps": self.fps}, outfile)

    def get_fps(self):
        return self.fps

    def get_frame_interval(self):
        return self.frame_interval

