# Noughts and Crosses
# Copyright (C) Paul Brook <paul@nowt.org>
# Released under the terms of the GNU General Public License version 3

import random
import cubehelper
import math
import numpy
import itertools
import httpinput

DT = 1.0/25

WHITE = 0xffffff
RED = 0xff0000
BLUE = 0x0000ff

def diagonals():
    for x in range(0, 4):
        for y in range(0, 4):
            yield [(x, y, i) for i in range(0,4)]
            yield [(x, i, y) for i in range(0,4)]
            yield [(i, x, y) for i in range(0,4)]
        yield [(x, i, i) for i in range(0,4)]
        yield [(x, i, i) for i in range(0,4)]
        yield [(x, i, 3-i) for i in range(0,4)]
    yield [(i, i, i) for i in range(0,4)]
    yield [(i, i, 3-i) for i in range(0,4)]
    yield [(i, 3-i, i) for i in range(0,4)]
    yield [(i, 3-i, i) for i in range(0,4)]

class Pattern(object):
    def init(self):
        if self.arg is None:
            raise StopIteration
        port = int(self.arg)
        self.grid = numpy.zeros((4,4,4), 'i')
        self.double_buffer = True
        self.cursor = [0, 0, 0]
        self.ccount = 0.0
        self.cdelta = 5.0
        self.coffset_iter = itertools.cycle([(0,0), (0, 1), (1, 1), (1, 0)])
        self.coffset = next(self.coffset_iter)
        self.cnext = next(self.coffset_iter)
        self.current_player = 0
        self.won_line = None
        buttons = [['up', 'out'], ['down', 'in'], ['left', 'right'], ['place']]
        httpinput.StartHTTP(port, 'OXO', buttons, self.action)
        return DT

    def check_won(self):
        val = self.current_player + 1
        for l in diagonals():
            won = True
            for (x, y, z) in l:
                if self.grid[x, y, z] != val:
                    won = False
                    break
            if won:
                self.won_line = l;
                return True
        return False

    def move_cursor(self, axis, val):
        x = self.cursor[axis] + val;
        if (x >= 0) and (x < 4):
            self.cursor[axis] = x;

    def set_block(self):
        pos = tuple(self.cursor)
        if self.grid[pos] != 0:
            return
        self.grid[pos] = self.current_player + 1
        if not self.check_won():
            self.current_player = 1 - self.current_player

    def action(self, action):
        al = action.split('/')
        if len(al) != 3:
            return
        player = int(al[1]) - 1
        if (player < 0) or (player > 2):
            raise ValueError
        if player != self.current_player:
            return
        if self.won_line is not None:
            return
        cmd = al[2]
        if cmd == 'up':
            self.move_cursor(2, 1)
        elif cmd == 'down':
            self.move_cursor(2, -1)
        elif cmd == 'left':
            self.move_cursor(0, -1)
        elif cmd == 'right':
            self.move_cursor(0, 1)
        elif cmd == 'in':
            self.move_cursor(1, -1)
        elif cmd == 'out':
            self.move_cursor(1, 1)
        elif cmd == 'place':
            self.set_block()
        else:
            raise ValueError

    def box(self, x, y, z, color):
        x *= 2
        y *= 2
        z *= 2
        for i in range(x, x + 2):
            for j in range(y, y + 2):
                for k in range(z, z + 2):
                    self.cube.set_pixel((i, j, k), color)

    def tick(self):
        def draw_cursor(pos):
            (x, y, z) = pos
            base = color_lut[self.grid[x, y, z]]
            x *= 2
            y *= 2
            z *= 2
            color = cubehelper.mix_color(base, WHITE, 1.0 - self.ccount)
            (i, j) = self.coffset
            self.cube.set_pixel((x+i,y+j,z), color)
            self.cube.set_pixel((x+1-i,y+1-j,z+1), color)
            color = cubehelper.mix_color(base, WHITE, self.ccount)
            (i, j) = self.cnext
            self.cube.set_pixel((x+i,y+j,z), color)
            self.cube.set_pixel((x+1-i,y+1-j,z+1), color)

        color_lut = [0, RED, BLUE]
        dim = 2 - self.current_player
        color_lut[dim] = cubehelper.mix_color(0, color_lut[dim], 0.20)
        for y in range(0, 4):
            for z in range(0, 4):
                for x in range(0, 4):
                    color = color_lut[self.grid[x, y, z]]
                    self.box(x, y, z, color)
        if self.won_line is None:
            draw_cursor(self.cursor)
        else:
            for pos in self.won_line:
                draw_cursor(pos)
        self.ccount += self.cdelta * DT
        if self.ccount > 1.0:
            self.ccount -= 1.0
            self.coffset = self.cnext
            self.cnext = next(self.coffset_iter)
