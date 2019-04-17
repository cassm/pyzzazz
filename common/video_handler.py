import os


class VideoHandler:
    def __init__(self, video_path):
        if not os.path.isdir(video_path):
            raise Exception("ERROR: the directory {} does not exist".format(video_path))

        self.videos = os.listdir(video_path)
        print(self.videos)

    def update(self, time):
        pass

    def receive_command(self, command):
        if command["type"] == "video":
            name = command["name"]
            if name not in self.videos:
                raise Exception("Unknown video file ", name)

    def sample(self, flat_mapping):
        pass
