# Fill the cube with a solid colour, starting from random corners
# Copyright (C) Alex Silcock <alex@alexsilcock.net>
# Released under the terms of the GNU General Public License version 3

from re import S
import cubehelper
import math
import random

# range is inclusive
def in_range(x, a, b):
    return (x >= a) and (x <= b)

class Pattern(object):
    def init(self):
        self.double_buffer = True
        # Vertices:
        # bottom layer
        # 2--6
        # |  |
        # 0--4
        #
        # top layer
        # 3--7
        # |  |
        # 1--5

        # cs = self.cube.size-1

        # self.corners = [
        #     (0, 0, 0),     # 0
        #     (0, 0, cs),    # 1
        #     (0, cs, 0),    # 2
        #     (0, cs, cs),   # 3
        #     (cs, 0, 0),    # 4
        #     (cs, 0, cs),   # 5
        #     (cs, cs, 0),   # 6
        #     (cs, cs, cs),  # 7
        # ]

        # self.filling_color = 0
        # self.corner_index = None
        # self.restart()
        self.box = self.boxGen()
        self.currRadius = 3
        self.tick()
        return 0.6 / self.cube.size

    # def restart(self):
    #     self.offset = 0
    #     new_corner_index = self.corner_index
    #     while self.corner_index == new_corner_index:
    #         new_corner_index = random.randrange(0, 8)
    #     self.corner_index = new_corner_index
    #     self.corner = self.corners[self.corner_index]
    #     self.filling_color = cubehelper.random_color(self.filling_color)

    def boxGen(self):
        while True:
            for y in range(self.cube.size-1):
                yield (0, y)

            for x in range(self.cube.size-1):
                yield (x, 7)

            for y in range(self.cube.size-1):
                yield (7, 7-y)

            for x in range(self.cube.size-1):
                yield (7-x, 0)

    
    def distance3d(self, p1, p2):
        """Return the 3-dimension distance between two points"""
        delta0 = p1[0] - p2[0]
        delta1 = p1[1] - p2[1]
        delta2 = p1[2] - p2[2]
        return math.sqrt(delta0**2 + delta1**2 + delta2**2)

    def boundingCube(self, centre, radius):
        clamp = lambda n, minn, maxn: max(min(maxn, n), minn)
        mx = self.cube.size

        rad = math.ceil(radius)
        for x in range(clamp(centre[0]-rad, 0, mx), clamp(centre[0]+rad+1, 0, mx)):
            for y in range(clamp(centre[1]-rad, 0, mx), clamp(centre[1]+rad+1, 0, mx)):
                for z in range(clamp(centre[2]-rad, 0, mx), clamp(centre[2]+rad+1, 0, mx)):
                    yield (x, y, z)

    def drawSphere(self, centre, r):
        """Draw a sphere centered around a point"""
        for coord in self.boundingCube(centre, r):
            di = self.distance3d(centre, coord)
            if di <= r:
                self.cube.set_pixel(coord, (1.0, 0.0, 0.0))

    def tick(self):
        self.cube.clear()

        # pix = next(self.box)
        # print(pix)
        # for coord in cubehelper.line((0, 0, 0), (pix[0], pix[1], 7)):
        #     self.cube.set_pixel(coord, (1.0, 1.0, 1.0))

        # self.currRadius += 0.2
        self.drawSphere((3, 3, 3), self.currRadius)

        # pos = self.corner
        # outer = self.offset
        # inner = self.offset - 4

        # for y in range(self.cube.size):
        #     dy = abs(y - pos[1])
        #     for x in range(self.cube.size):
        #         dx = abs(x - pos[0])
        #         for z in range(self.cube.size):
        #             dz = abs(z - pos[2])
        #             if max(dx, dy, dz) >= inner and max(dx, dy, dz) <= outer:
        #                 color = self.filling_color
        #             else:
        #                 color = 0
        #             self.cube.set_pixel((x, y, z), color)

        # if inner == self.cube.size:
        #     self.restart()
        #     raise StopIteration
        # else:
        #     self.offset += 1
