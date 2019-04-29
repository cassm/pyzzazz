import usb.core
import usb.util
import psutil
import sys
from pathlib import Path
import usb.core
import usb.util


class ExternalDrive:

    def _init_(self):

        self._conf_search_term = 'conf.json'
        self._palette_search_term = '*.bmp'
        self._op_system = sys.platform
        self._mount_points = get_mount_points()
        self.conf = get_conf_json()



    def read_files(self):
        files = []

        return files



    def find_conf_files(self):

        paths = []

        for directory in self._mount_points:
            paths.extend(list(Path(directory).glob(self._conf_search_term)))

        return paths


    def get_mount_points(self):
        """
        MAC OS removable volume mount-point finder
        Output: list(str), eg ["/Volumes/Flash", "/Volumes/Stick"]
        """
        if self._op_system == 'darwin':
            disk_drives = subprocess.check_output(["diskutil", "info", "-all"], text=True)


        removables = re.findall(r'.Volumes.\w*', disk_drives)

        if len(removables) == 0:
            raise Exception('Could not find a USB to read')

        else:
            return removables





class FindRemovable(object):
    """
    usb device class callable matcher for use by (and courtesy of) usb.core.find;
    necessary because devices keep their class tags in different config areas
    """

    def __init__(self, class_):
        self._class = class_

    def __call__(self, device):

        if device.bDeviceClass == self._class:
            return True

        for configuration in device:
            interface = usb.util.find_descriptor(
                                        configuration,
                                        bInterfaceClass=self._class)

            if interface is not None:
                return True

        return False


def mass_storage_check(device_class=8):
    """
    Searches through USB buses to check for removable storage.
    device_class - literally number 8, which is USB for "mass storage".
    Returns a list of dicts with some particulars, indexed by manufacturer
    example output: [{'Kingston': {'port': 11, 'bus': 20, 'address': 2}}]
    """

    removables_generator = usb.core.find(find_all=1,
                                         custom_match=FindRemovable(device_class))

    removables = [{device.manufacturer: {"port":        device.port_number,
                                         "bus":         device.bus,
                                         "address":     device.address}
                                                    for device in removables_generator}]

    if len(removables) == 0:
        raise Exception('Could not find a USB stick')

    else:
        return removables








def get_palettes(path_anchors, palettes_search_str):

    return list(Path(path_anchors).glob(palettes_search_str))


print(get_conf_json('/Volumes/KINGSTON', 'conf.json'))
print(get_palettes('/Volumes/KINGSTON', '*.bmp'))
