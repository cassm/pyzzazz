import re
import inspect
import patterns
from patterns.pattern import Pattern


class PatternHandler:
    def __init__(self):
        self.patterns = {}

        # find all submodules of pattern module and store them by name
        submodules = [obj for name, obj in inspect.getmembers(patterns) if inspect.ismodule(obj)]
        for submodule in submodules:
            for name, obj in inspect.getmembers(submodule):
                if inspect.isclass(obj) and issubclass(obj, Pattern):
                    if obj != Pattern:
                        # convert camelcase class name to snakecase identifier
                        snake_case_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
                        snake_case_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case_name)
                        snake_case_name = snake_case_name.lower()
                        self.patterns[snake_case_name] = obj

    def get_patterns(self):
        return self.patterns
