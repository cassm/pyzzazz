import os
from patterns.pattern import Pattern
from common.dynamic_loader import get_module_classes
from common.utils import camel_to_snake


class PatternHandler:
    def __init__(self):
        self.patterns = {}

        cwd = os.path.dirname(__file__)
        patterns_dir = os.path.join(cwd, '..', 'patterns')
        classes = get_module_classes(patterns_dir)
        for name, obj in classes.items():
            if issubclass(obj, Pattern) and obj != Pattern:
                snake_case_name = camel_to_snake(name)
                self.patterns[snake_case_name] = obj

    def get_patterns(self):
        return self.patterns
