# SPDX-License-Identifier: MIT
# Licence: MIT

# These imports are recommended
import cubehelper
import math
import random

# Define our pattern object
class Pattern(object):
    def init(self):
        # Ensure the cube double buffers
        self.double_buffer = True
        return 1
       
    def tick(self):
        # Generate two random points
        p1 = [random.randrange(0, self.cube.size) for _ in range(3)]
        p2 = [random.randrange(0, self.cube.size) for _ in range(3)]
        # Pick a random color
        color = cubehelper.random_color()
        # Fill in all points on line with color
        for p in cubehelper.line(p1, p2):
            self.cube.set_pixel(p, color)
        pass