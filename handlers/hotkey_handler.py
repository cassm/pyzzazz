import math
import sys
import select


class HotKeyHandler:
    def __init__(self, fixtures, calibration_handler):
        self.fixtures = fixtures
        self.calibration_handler = calibration_handler
        self.exit = False

    def poll(self):
        while self.is_data():
            c = sys.stdin.read(1)

            if c == "c":
                for fixture in self.fixtures:
                    fixture.toggle_calibrate()

            elif c == " ":
                self.calibration_handler.increment_selection()

            elif c == "h":
                self.calibration_handler.add_angle_to_selection(math.pi/-6.0)

            elif c == "l":
                self.calibration_handler.add_angle_to_selection(math.pi/6.0)

            elif c == 'q':
                self.exit = True

    def is_data(self):
        return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])
