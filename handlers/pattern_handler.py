import re
import os
from patterns.pattern import Pattern
from common.dynamic_loader import get_module_classes


class PatternHandler:
    def __init__(self):
        self.patterns = {}

        cwd = os.path.dirname(__file__)
        patterns_dir = os.path.join(cwd, '..', 'patterns')
        classes = get_module_classes(patterns_dir)
        for name, obj in classes.items():
            if issubclass(obj, Pattern) and obj != Pattern:
                # convert camelcase class name to snakecase identifier
                snake_case_name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
                snake_case_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake_case_name)
                snake_case_name = snake_case_name.lower()
                self.patterns[snake_case_name] = obj


    def get_patterns(self):
        return self.patterns
