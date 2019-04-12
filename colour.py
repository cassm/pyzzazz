from operator import gt, lt, eq, le, ne, ge
class Colour:
    def __init__(self, r=0.0, g=0.0, b=0.0):
        self.r = r
        self.g = g
        self.b = b

        self.__radd__ = self.__add__
        self.__rsub__ = self.__sub__

    def __mul__(self, o):
        if isinstance(o, Colour):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r * o.r, self.g * o.g, self.b * o.b))

        elif isinstance(o, int) or isinstance(o, float):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r * o, self.g * o, self.b * o))

        else:
            raise Exception("Must multiply Colour by either Colour, int, or float")

    def __imul__(self, o):
        if isinstance(o, Colour):
            self.r = max(self.r * o.r, 0)
            self.g = max(self.g * o.g, 0)
            self.b = max(self.b * o.b, 0)

        elif isinstance(o, int) or isinstance(o, float):
            self.r = max(self.r * o, 0)
            self.g = max(self.g * o, 0)
            self.b = max(self.b * o, 0)

        else:
            raise Exception("Must multiply Colour by either Colour, int, or float")

        return self

    def __truediv__(self, o):
        if isinstance(o, Colour):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r / o.r, self.g / o.g, self.b / o.b))

        elif isinstance(o, int) or isinstance(o, float):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r / o, self.g / o, self.b / o))

        else:
            raise Exception("Must divide Colour by either Colour, int, or float")

    def __floordiv__(self, o):
        if isinstance(o, Colour):
            return Colour(0, 0, 0).channelwise_max(Colour(int(self.r / o.r), int(self.g / o.g), int(self.b / o.b)))

        elif isinstance(o, int) or isinstance(o, float):
            return Colour(0, 0, 0).channelwise_max(Colour(int(self.r / o), int(self.g / o), int(self.b / o)))

        else:
            raise Exception("Must divide Colour by either Colour, int, or float")

    def __idiv__(self, o):
        if isinstance(o, Colour):
            self.r = max(self.r / o.r, 0)
            self.g = max(self.g / o.g, 0)
            self.b = max(self.b / o.b, 0)

        elif isinstance(o, int) or isinstance(o, float):
            self.r = max(self.r / o, 0)
            self.g = max(self.g / o, 0)
            self.b = max(self.b / o, 0)

        else:
            raise Exception("Must divide Colour by either Colour, int, or float")

        return self

    def __add__(self, o):
        if isinstance(o, Colour):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r + o.r, self.g + o.g, self.b + o.b))

        elif isinstance(o, int) or isinstance(o, float):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r + o, self.g + o, self.b + o))

        else:
            raise Exception("Must add Colour to either Colour, int, or float")

    def __iadd__(self, o):
        if isinstance(o, Colour):
            self.r = max(self.r + o.r, 0)
            self.g = max(self.g + o.g, 0)
            self.b = max(self.b + o.b, 0)

        elif isinstance(o, int) or isinstance(o, float):
            self.r = max(self.r + o, 0)
            self.g = max(self.g + o, 0)
            self.b = max(self.b + o, 0)

        else:
            raise Exception("Must add Colour to either Colour, int, or float")

        return self

    def __sub__(self, o):
        if isinstance(o, Colour):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r - o.r, self.g - o.g, self.b - o.b))

        elif isinstance(o, int) or isinstance(o, float):
            return Colour(0, 0, 0).channelwise_max(Colour(self.r - o, self.g - o, self.b - o))

        else:
            raise Exception("Must subtract either Colour, int, or float from Colour")

    def __isub__(self, o):
        if isinstance(o, Colour):
            self.r = max(self.r - o.r, 0)
            self.g = max(self.g - o.g, 0)
            self.b = max(self.b - o.b, 0)

        elif isinstance(o, int) or isinstance(o, float):
            self.r = max(self.r - o, 0)
            self.g = max(self.g - o, 0)
            self.b = max(self.b - o, 0)

        else:
            raise Exception("Must subtract either Colour, int, or float from Colour")

        return self

    def channelwise_max(self, o):
        return Colour(max(self.r, o.r), max(self.g, o.g), max(self.b, o.b))

    def channelwise_min(self, o):
        return Colour(min(self.r, o.r), min(self.g, o.g), min(self.b, o.b))

    def __iter__(self):
        """
        >>> list(Colour(15, 7, 8))
        [15, 7, 8]
        >>> for led in (Colour(15, 7, 8)):
        ...     print(led)
        ... 
        15
        7
        8
        """
        return iter([self.r, self.g, self.b])

    def eq(self, o):
        assert isinstance(o, Colour), 'must compare Colour to Colour'
        return self.r > o.r and self.g > o.g and self.b > o.b

    def ne(self, o):
        assert isinstance(o, Colour), 'must compare Colour to Colour'
        return self.r != o.r and self.g != o.g and self.b != o.b
    
    def __repr__(self):
        """
        >>> c1 = Colour(15, 7, 8)
        >>> c1
        Colour(r: 15, g: 7, b:8)
        """
        return 'Colour(r: {0:g}, g: {1:g}, b:{2:g})'.format(self.r, self.g, self.b)

    def __str__(self):
        """
        >>> str(Colour(16, 0, 0))
        '(16, 0, 0)'
        >>> print(Colour(16, 0, 0))
        (16, 0, 0)
        """

        return '({0:g}, {1:g}, {2:g})'.format(self.r, self.g, self.b)
