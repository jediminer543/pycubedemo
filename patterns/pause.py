import random
import cubehelper
import os
import math
import pygame

class Pattern(object):
    def init(self):
        self.timer = 0.0    
        return 1.0 / 10

    def tick(self):
        self.cube.clear()
        raise StopIteration
