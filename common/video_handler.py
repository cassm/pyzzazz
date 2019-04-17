import os
import cv2


class VideoHandler:
    def __init__(self, video_path):
        if not os.path.isdir(video_path):
            raise Exception("ERROR: the directory {} does not exist".format(video_path))

        self.videos = dict()

        for video_name in os.listdir(video_path):
            if not video_name.startswith("."):
                file_path = os.path.join(video_path, video_name)
                self.videos[video_name] = file_path

        self.scaling_factor = 0

        self.width_offset = 0
        self.height_offset = 0
        self.vid_length = 1

        self._switch_to_video(list(self.videos.keys())[0])

    def _switch_to_video(self, name):
        if name not in self.videos.keys():
            raise Exception("Unknown video ", name)

        self.current_video = self.videos[name]
        self.vidcap = cv2.VideoCapture(self.current_video)

        self.vidcap.set(cv2.CAP_PROP_POS_AVI_RATIO, 1)
        self.vid_length = self.vidcap.get(cv2.CAP_PROP_POS_MSEC)

        self._update_sampling_factors()

    def _update_sampling_factors(self):
        width = self.vidcap.get(3)
        height = self.vidcap.get(4)

        if width < height:
            self.height_offset = (height - width) / 2
            self.width_offset = 0
        elif height < width:
            self.width_offset = (width - height) / 2
            self.height_offset = 0
        else:
            self.width_offset = 0
            self.height_offset = 0

        self.scaling_factor = min(width, height) - 1

    def update(self, time):
        self.vidcap.set(cv2.CAP_PROP_POS_MSEC, (time*1000) % self.vid_length)

        success, image = self.vidcap.read()

        if success:
            self.frame = image
        if not success:
            raise Exception("Failed to read video frame")

    def receive_command(self, command):
        if command["type"] == "pattern" and command["name"] == "map_video":
            name = command["video_name"]

            self._switch_to_video(name)

    def sample(self, flat_mapping):
        mapped_x = int(flat_mapping[0]*self.scaling_factor + self.width_offset)
        mapped_y = int(flat_mapping[1]*self.scaling_factor + self.height_offset)

        return list(self.frame[mapped_y, mapped_x])
