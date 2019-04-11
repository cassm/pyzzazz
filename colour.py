from operator import gt, lt, eq, le, ne, ge
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
        assert type(o) == Colour, 'must compare Colour to Colour'
        return Colour(max(self.r, o.r), max(self.g, o.g), max(self.b, o.b))

    def min(self, o):
        return Colour(min(self.r, o.r), min(self.g, o.g), min(self.b, o.b))

    #FIXME returns "Colour object is not iterable"
    def list(self):
        '''
        >>> list(Colour(15, 7, 8))
        [15, 7, 8]
        '''
        return [self.r, self.g, self.b]

    def gt(self, o):
        assert type(o) == Colour, 'must compare Colour to Colour'
        return self.r > o.r and self.g > o.g and self.b > o.b

    def lt(self, o):
        assert type(o) == Colour, 'must compare Colour to Colour'
        return self.r < o.r and self.g < o.g and self.b < o.b

    def eq(self, o):
        assert type(o) == Colour, 'must compare Colour to Colour'
        return self.r > o.r and self.g > o.g and self.b > o.b

    def ge(self, o):
        assert type(o) == Colour, 'must compare Colour to Colour'
        return self.r >= o.r and self.g >= o.g and self.b >= o.b

    def le(self, o):
        assert type(o) == Colour, 'must compare Colour to Colour'
        return self.r <= o.r and self.g <= o.g and self.b <= o.b

    def ne(self, o):
        assert type(o) == Colour, 'must compare Colour to Colour'
        return self.r != o.r and self.g != o.g and self.b != o.b
    
    def __repr__(self):
        '''
        >>> c1 = Colour(15, 7, 8)
        >>> c1
        Colour(r: 15, g: 7, b:8)
        '''
        return 'Colour(r: {0:g}, g: {1:g}, b:{2:g})'.format(self.r, self.g, self.b)

    def __str__(self):
        '''
        >>> str(Colour(16, 0, 0))
        '(16, 0, 0)'
        >>> print(Colour(16, 0, 0))
        (16, 0, 0)
        '''

        return '({0:g}, {1:g}, {2:g})'.format(self.r, self.g, self.b)