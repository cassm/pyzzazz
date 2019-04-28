from patterns.pattern import Pattern


class MapVideo(Pattern):
    def __init__(self, image_src):
        self.video_handler = image_src

    def get_pixel_colour(self, pixels, index, time, palette_handler, palette_name, master_brightness):
        return list(value * master_brightness for value in self.video_handler.sample(pixels[index].flat_mapping))
