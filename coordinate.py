import math


class Cartesian:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, o):
        return Cartesian(self.x + o.x, self.y + o.y, self.z + o.z)

    __radd__ = __add__

    def __iadd__(self, o):
        self.x += o.x
        self.y += o.y
        self.z += o.z
        return self

    def __sub__(self, o):
        return Cartesian(self.x - o.x, self.y - o.y, self.z - o.z)

    __rsub__ = __sub__

    def __isub__(self, o):
        self.x -= o.x
        self.y -= o.y
        self.z -= o.z
        return self

    def __eq__(self, o):
        return self.x == o.x and self.y == o.y and self.z == o.z

    def get_magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

    def get_spherical(self):
        r = self.get_magnitude()
        theta = math.atan(self.y/self.x)
        phi = math.atan(math.sqrt(self.x ** 2 + self.y ** 2) / self.z)

        return Spherical(r, theta, phi)

    def list(self):
        return [self.x, self.y, self.z]


class Spherical:
    def __init__(self, r, theta, phi):
        self.r = r
        self.theta = theta
        self.phi = phi

    def add_phi(self, angle):
        self.phi += angle

        while self.phi < 0:
            self.phi += 2*math.pi

        self.phi %= (2*math.pi)

    def add_theta(self, angle):
        self.theta += angle

        while self.theta < 0:
            self.theta += 2*math.pi

        self.theta %= (2*math.pi)

    def get_cartesian(self):
        x = self.r * math.sin(self.phi) * math.cos(self.theta)
        y = self.r * math.sin(self.phi) * math.sin(self.theta)
        z = self.r * math.cos(self.phi)

        return Cartesian(x, y, z)

    def list(self):
        return [self.r, self.theta, self.phi]


class Coordinate:
    def __init__(self, local_origin, local_cartesian=None, local_spherical=None):
        self._local_origin = local_origin

        if local_cartesian and not local_spherical:
            self._local_cartesian = local_cartesian
            self._local_spherical = self._local_cartesian.get_spherical()

        elif local_spherical and not local_cartesian:
            self._local_spherical = local_spherical
            self._local_cartesian = self._local_spherical.get_cartesian()

        else:
            raise Exception("Coordinate: must initialise with either spherical or cartesian, not neither or both")

        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def __eq__(self, o):
        return self._global_cartesian == o.get_cartesian()

    def add_cartesian(self, o):
        self._local_cartesian += o

        self._local_spherical = self._local_cartesian.get_spherical()
        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def get_global_delta(self):
        return self._global_delta

    def get_local_origin(self):
        return self._local_origin

    # FIXME change these names?
    # changes the local origin and leaves the point static in the LOCAL frame
    def set_local_origin(self, o):
        self._local_origin = o
        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    # changes the local origin and leaves the point static in the GLOBAL frame
    def make_relative_to(self, local_origin):
        local_origin_delta = local_origin - self._local_origin
        self._local_cartesian += local_origin_delta
        self._local_spherical = self._local_cartesian.get_spherical()

    def get_global_spherical(self):
        return self._global_spherical

    def set_global_spherical(self, o):
        self._global_spherical = o
        self._global_cartesian = self._global_spherical.get_cartesian()
        self._local_cartesian = self._global_cartesian - self._local_origin
        self._local_spherical = self._local_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def get_global_cartesian(self):
        return self._global_cartesian

    def set_global_cartesian(self, o):
        self._global_cartesian = o
        self._global_spherical = self._global_cartesian.get_spherical()
        self._local_cartesian = self._global_cartesian - self._local_origin
        self._local_spherical = self._local_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def get_local_spherical(self):
        return self._local_spherical

    def set_local_spherical(self, o):
        self._local_spherical = o
        self._local_cartesian = self._local_spherical.get_cartesian()
        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def get_local_cartesian(self):
        return self._local_cartesian

    def set_local_cartesian(self, o):
        self._local_cartesian = o
        self._local_spherical = self._local_cartesian.get_spherical()
        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def rotate_theta_global(self, angle):
        # must rotate local then global
        self.rotate_phi_local(angle)

        new_origin = self._local_origin.get_spherical()
        new_origin.add_theta(angle)
        self._local_origin = new_origin.get_cartesian()

        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def rotate_phi_global(self, angle):
        # must rotate local then global
        self.rotate_phi_local(angle)

        new_origin = self._local_origin.get_spherical()
        new_origin.add_phi(angle)
        self._local_origin = new_origin.get_cartesian()

        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def rotate_phi_local(self, angle):
        self._local_spherical.add_phi(angle)
        self._local_cartesian = self._local_spherical.get_cartesian()
        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def rotate_theta_local(self, angle):
        self._local_spherical.add_theta(angle)
        self._local_cartesian = self._local_spherical.get_cartesian()
        self._global_cartesian = self._local_cartesian + self._local_origin
        self._global_spherical = self._global_cartesian.get_spherical()
        self._global_delta = self._cartesian_delta(Cartesian(0, 0, 0))

    def _cartesian_delta(self, o):
        cartesian_delta = self._global_cartesian - o
        return cartesian_delta.get_magnitude
