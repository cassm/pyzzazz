class Colour:
    def __init__(self, r=0, g=0, b=0):
        self.r = r
        self.g = g
        self.b = b

        self.__radd__ = self.__add__
        self.__rsub__ = self.__sub__

    def __mul__(self, o):
        return Colour(max(self.r * o, 0), max(self.g * o, 0), max(self.b * o, 0))

    def __imul__(self, o):
        self.r = max(self.r * o, 0)
        self.g = max(self.g * o, 0)
        self.b = max(self.b * o, 0)
        return self

    def __div__(self, o):
        return Colour(max(self.r * o, 0), max(self.g * o, 0), max(self.b * o, 0))

    def __idiv__(self, o):
        self.r = max(self.r / o, 0)
        self.g = max(self.g / o, 0)
        self.b = max(self.b / o, 0)
        return self

    def __add__(self, o):
        return Colour(max(self.r + o.r, 0), max(self.g + o.g, 0), max(self.b + o.b, 0))

    def __iadd__(self, o):
        self.r = max(self.r + o.r, 0)
        self.g = max(self.g + o.g, 0)
        self.b = max(self.b + o.b, 0)
        return self

    def __sub__(self, o):
        return Colour(max(self.r - o.r, 0), max(self.g - o.g, 0), max(self.b - o.b, 0))

    def __isub__(self, o):
        self.r = max(self.r - o.r, 0)
        self.g = max(self.g - o.g, 0)
        self.b = max(self.b - o.b, 0)
        return self

    def max(self, o):
        return Colour(max(self.r, o.r), max(self.g, o.g), max(self.b, o.b))

    def min(self, o):
        return Colour(min(self.r, o.r), min(self.g, o.g), min(self.b, o.b))

    def list(self):
        return [self.r, self.g, self.b]


