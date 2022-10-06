# Fill the cube with a solid colour, starting from random corners
# Copyright (C) Alex Silcock <alex@alexsilcock.net>
# Released under the terms of the GNU General Public License version 3

from re import S
import cubehelper
import math
import random

ANTIALIAS_DIST = 0.2

class Pattern(object):
    def init(self):
        self.double_buffer = True
        self.box = self.boxGen()
        self.currRadius = 1.5
        self.ball_x = 0
        self.ball_y = 3
        self.ball_z = 3
        self.interval = 0.4 / self.cube.size
        self.elapsed = 0
        self.tick()
        return self.interval

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
        for x in range(clamp(math.floor(centre[0])-rad, 0, mx), clamp(math.ceil(centre[0])+rad+1, 0, mx)):
            for y in range(clamp(math.floor(centre[1])-rad, 0, mx), clamp(math.ceil(centre[1])+rad+1, 0, mx)):
                for z in range(clamp(math.floor(centre[2])-rad, 0, mx), clamp(math.ceil(centre[2])+rad+1, 0, mx)):
                    yield (x, y, z)

    def drawSphere(self, centre, r, color):
        """Draw a sphere centered around a point"""
        for coord in self.boundingCube(centre, r):
            di = self.distance3d(centre, coord)
            if di <= r:
                self.cube.set_pixel(coord, color)
            elif di <= r+ANTIALIAS_DIST:
                # antialias
                how_bright = 1.0 - (di - r)/ANTIALIAS_DIST
                self.cube.set_pixel(coord, (color[0]*how_bright, color[1]*how_bright, color[2]*how_bright))

    def tick(self):
        self.cube.clear()

        self.ball_x = 3.5 + math.sin(self.elapsed*3)*2.5
        self.ball_y = 3.5 + math.cos(self.elapsed*3)*2.5
        self.ball_z = 3.5 + math.sin(self.elapsed*5.2)

        self.drawSphere((self.ball_x, self.ball_y, self.ball_z), self.currRadius, (1.0, 0.0, 0.0))

        if (self.ball_x >= 10):
            self.ball_x = -3

        if (self.ball_y >= 10):
            self.ball_y = -3

        self.elapsed += self.interval