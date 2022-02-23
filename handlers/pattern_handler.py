import re
import os
import patterns
from inspect import isclass
from pkgutil import iter_modules
from importlib import import_module
from patterns.pattern import Pattern


class PatternHandler:
    def __init__(self):
        self.patterns = {}

        cwd = os.path.dirname(__file__)
        patterns_dir = os.path.join(cwd, '..', 'patterns')

        # find all subclasses of Pattern and store them by name
        for (_, module_name, _) in iter_modules([str(patterns_dir)]):
            module = import_module(f"patterns.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isclass(attr) and issubclass(attr, Pattern) and attr != Pattern:
                    # convert camelcase class name to snakecase identifier
                    snake_case_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', attr_name)
                    snake_case_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case_name)
                    snake_case_name = snake_case_name.lower()
                    self.patterns[snake_case_name] = attr


    def get_patterns(self):
        return self.patterns
