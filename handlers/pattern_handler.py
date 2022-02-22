import inspect
import patterns
from patterns.pattern import Pattern


class PatternHandler:
    def __init__(self):
        self.patterns = {}

        submodules = [obj for name, obj in inspect.getmembers(patterns) if inspect.ismodule(obj)]
        for submodule in submodules:
            for name, obj in inspect.getmembers(submodule):
                if inspect.isclass(obj) and issubclass(obj, Pattern):
                    if obj != Pattern:
                        self.patterns[name.lower()] = obj
