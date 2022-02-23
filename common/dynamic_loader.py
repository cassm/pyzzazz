from pkgutil import iter_modules
from importlib import import_module
from inspect import isclass
from os.path import basename


def get_module_classes(module_path):
    classes = {}

    # find all subclasses of Overlay and store them by name
    for (_, module_name, _) in iter_modules([str(module_path)]):
        module = import_module(f"{basename(module_path)}.{module_name}")
        for attr_name in dir(module):
            attr = getattr(module, attr_name)

            if isclass(attr):
                classes[attr_name] = attr

    return classes
