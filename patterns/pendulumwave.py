import random
import math
import cubehelper
import pygame
import os

TOTAL_TIME = 80.0
MINICYCLES = 20.0

def loadsounds(dirname, namelist):
    sounds = []
    for name in namelist:
        newsound = pygame.mixer.Sound(dirname + name + '.wav')
        sounds.append(newsound)
    return sounds

class Pattern(object):
    def init(self):
        self.pendarray = []
        pygame.init()
        pygame.mixer.init( )
        pygame.mixer.set_num_channels(64)
        self.pendsounds = loadsounds('patterns/pends/', ['plinks%d' %n for n in range(16)])
        for n in range(0, 16):
            self.pendarray.append(self.startpos(n))
        self.timer = 0.0
        return 1.0 / 20

    def tick(self):
        self.cube.clear()
        self.timer += 0.05
        for pend in self.pendarray:
            self.move(pend)
            self.draw(pend)
            print pend
	if self.timer > 100:
		raise StopIteration
        print self.timer

# define starting position x,y,z,period, initialise lasttime, color, pendnumber
    def startpos(self, pendnum):
        start = [0,  int((pendnum // 4) * 2 ), int((pendnum % 4) * 2), TOTAL_TIME / (MINICYCLES + pendnum), 0.0, ((pendnum % 2) * 255, 0, (1 - (pendnum % 2)) * 255), pendnum]
        return start

# # check to see if pend should move
    def move(self, pend):
        timesince = self.timer - pend[4]
        pos = int((timesince / pend[3]) * 14)
        if pos == 0.0:
                self.pendsounds[pend[6]].play()
        if pos > 6:
            pend[0] = 13 - int(pos)
        else:
            pend[0] = int(pos)
        if timesince >= pend[3]:
            pend[4] += pend[3]
            pend[0] = 0

# draw pend to cube
    def draw(self, pend):
        for x in range(0,2):
            for y in range(0,2):
                for z in range(0,2):
                    self.cube.set_pixel( (int(pend[0] + x), int(pend[1] + y), int(pend[2] +z)), pend[5])
