import psutil
import sys
import subprocess
import re
from pathlib import Path

class ExternalDriveHandler:
    """An interface for getting config files off an external drive.
    Reads MacOS (Darwin) and Unix filesystems.
    Watch out for drives with extraneous .bmp and .mp4 files,
    it'll hoover them all up indiscriminately.

    - first make the drive

        drive = ExternalDrive()
        =>> Found 1 external filesystem(s): ['<path string>']

    - you can read config, palette and video paths separately;
        they each return a list of corresponding file paths (or an empty list)

        drive.read_palette_paths() => [PosixPath('/<...>/such_palette1.bmp', PosixPath('/<...>/such_palette2.bmp']
        drive.read_config_paths() => [PosixPath('/<...>/very_conf.json', PosixPath('/<...>/so_conf.json']
        drive.read_video_paths() => [PosixPath('/<...>/omg_video1.mp4', PosixPath('/<...>/omg_video2.mp4']

    - alternatively, get all the Path objects in one flat list

        drive.read_all_paths()
        =>> [   PosixPath('/<...>/such_palette1.bmp'),  <more palettes>,
                PosixPath('/<...>/conf_file1.json'),    <more configs>,
                PosixPath('/<...>/omg_video1.mp4')      <more mp4s>,
            ] etc
    """

    _config_search_term = '**/conf.json'
    _calibration_search_term = '**/calibration.json'
    _palette_search_term = '**/*.bmp'
    _video_search_term = "**/*.mp4"

    def __init__(self):
        self._config_files = []
        self._calibration_files = []
        self._palette_files = []
        self._video_files = []
        self.__find_files__()

    def read_all_paths(self):
        return sum([self._config_files, self._calibration_files, self._palette_files, self._video_files], [])

    def get_config_paths(self):
        return self._config_files

    def get_calibration_paths(self):
        return self._calibration_files

    def get_palette_paths(self):
        return self._palette_files

    def get_video_paths(self):
        return self._video_files

    def __find_files__(self):
        try:
            for directory in self.__get_mount_points__():
                self._config_files.extend(list(Path(directory).glob(self._config_search_term)))
                self._calibration_files.extend(list(Path(directory).glob(self._calibration_search_term)))
                self._palette_files.extend(list(Path(directory).glob(self._palette_search_term)))
                self._video_files.extend(list(Path(directory).glob(self._video_search_term)))

        except:
            pass

    def __get_mount_points__(self):
        if sys.platform == 'darwin':
            external_drives = subprocess.check_output(["diskutil", "list", "-plist", "external"], text=True)
            removables = re.findall(r'/Volumes/\w*', external_drives)

        elif sys.platform == 'linux':
            block_devices = subprocess.getoutput(["lsblk -o RM,TYPE,MOUNTPOINT"]).split("\n ")
            removables = [device.split(" ")[-1] for device in block_devices if device[0:6]=='1 part']

        if len(removables) == 0:
            raise Exception('Could not find a drive to read')

        else:
            print("Found {} external filesystem(s): {}".format(len(removables), removables))
            return removables

