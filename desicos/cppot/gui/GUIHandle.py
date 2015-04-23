"""TODO document"""

import math
import copy
from collections import namedtuple

from desicos.cppot.core.geom import ConeGeometry
from desicos.constants import TOL


class DataParameter(object):
    """TODO document"""
    def __init__(self, min_value, max_value, step, fix):
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.fix = fix

    def steps(self):
        return [self.min_value + i*self.step for i in range(0, self.num_steps())]

    def num_steps(self):
        if self.fix:
            return 1
        return int(math.floor((TOL + self.max_value - self.min_value) / self.step)) + 1


class DataHandle(object):
    """TODO document"""
    ATTRIBUTES = ('angle', 'width', 'start', 'var')

    def __init__(self):
        # Initialize with some default values
        self.width = DataParameter(100.0, 300.0, 10.0, False)
        self.start = DataParameter(250.0, 600.0, 10.0, False)
        self.angle = DataParameter(30.0, 45.0, 1.0, False)
        self.var = DataParameter(0.0, 1.0, 0.1, False)
        self.shape = 1
        self.cg = ConeGeometry(300.0, 400.0, math.radians(35.0), 70.0)

    def get_s(self):
        return (self.cg.s1, self.cg.s2, self.cg.s3, self.cg.s4)

    def get_r(self):
        return tuple(self.cg.sin_alpha * s for s in self.get_s())

    def get_z(self):
        return tuple((self.cg.rbot - r) / self.cg.tan_alpha for r in self.get_r())

    def make_copy(self):
        return copy.deepcopy(self)

    def get_as_table(self):
        table = []
        for attr in self.ATTRIBUTES:
            param = getattr(self, attr)
            table.append([param.min_value, param.max_value, param.step, int(param.fix)])
        table.append([self.shape])
        return table

    def load_from_table(self, table):
        # Fill DataHandle based on values in a table (loaded from csv)
        for i, attr in enumerate(('width', 'start', 'angle', 'var')):
            args = [float(table[i][0]), float(table[i][1]),
                    float(table[i][2]), bool(int(table[i][3]))]
            setattr(self, attr, DataParameter(*args))
        self.shape = int(table[4][0])

    def load_from(self, other):
        other = other.make_copy()
        self.width = other.width
        self.start = other.start
        self.angle = other.angle
        self.var = other.var
        self.shape = other.shape
        self.cg = other.cg

    @property
    def alphadeg(self):
        return math.degrees(self.cg.alpharad)

    @alphadeg.setter
    def alphadeg(self, value):
        self.cg.alpharad = math.radians(value)

    def num_calc(self):
        num_calc = self.width.num_steps()
        num_calc *= self.start.num_steps()
        num_calc *= self.angle.num_steps()
        num_calc *= self.var.num_steps()
        return num_calc


Result = namedtuple('Result', ['angle', 'start', 'width', 'var', 'Phi1',
                               'Phi2', 'Phi3', 'Phi4', 'num_pieces', 'R_DoC',
                               'R_Aeff' , 'R_cont', 'R_SumAeff', 'R_total'])

class ResultHandle(object):
    """TODO Document"""
    def __init__(self):
        self.results = []

    def add(self, *args, **kwargs):
        self.results.append(Result(*args, **kwargs))

    def get(self):
        return self.results

    def clear(self):
        self.results = []
