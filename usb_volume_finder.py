import usb.core
import usb.util
import psutil
from pathlib import Path

import usb.core
import usb.util


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


def get_mount_points():
    """
    MAC OS removable volume mount-point finder
    Output: list(str), eg ["/Volumes/Flash", "/Volumes/Stick"]
    """

    partitions = psutil.disk_partitions()
    mount_points = []

    for partition in partitions:
        root = partition.mountpoint

        if root.split("/")[1] == "Volumes":
            mount_points.append(root)

    if len(mount_points) == 0:
        raise Exception('Could not find a USB to read')

    else:
        return mount_points


def get_conf_json(path_anchor, conf_search_str):

    return list(Path(path_anchor).glob(conf_search_str))


def get_palettes(path_anchor, palettes_search_str):

    return list(Path(path_anchor).glob(palettes_search_str))


print(get_conf_json('/Volumes/KINGSTON', 'conf.json'))
print(get_palettes('/Volumes/KINGSTON', '*.bmp'))
