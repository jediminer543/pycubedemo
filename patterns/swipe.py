# Swipe a plane across the cube in all 3 dimensions
# Copyright (C) Paul Brook <paul@nowt.org>
# Released under the terms of the GNU General Public License version 3

import cubehelper

class Pattern(object):
    def init(self):
        self.phase = 0
        self.offset = -self.cube.size
        self.color = cubehelper.random_color()
        return (2.6086956522/2) / self.cube.size
    def tick(self):
        self.offset += 1
        p0 = self.phase
        p1 = (p0 + 1) % 3
        p2 = (p1 + 1) % 3
        pos = [0]*3
        off = [0]*3
        on = [0]*3
        on[p0] = 255
        for i in range(0, self.cube.size):
            if i == self.cube.size - (abs(self.offset) + 1):
                color = self.color
            else:
                color = off
            pos[p0] = i
            for j in range(0, self.cube.size):
                pos[p1] = j
                for k in range(0, self.cube.size):
                    pos[p2] = k
                    self.cube.set_pixel(pos, color)
        if self.offset == self.cube.size - 1:
            self.color = cubehelper.random_color()
            self.offset = 1 - self.cube.size
            self.phase += 1
            if self.phase == 3:
                self.phase = 0
            raise StopIteration
        if self.offset == 0:
            raise StopIteration
