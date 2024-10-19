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
        self.double_buffer = False
        self.progress = 0
        return 1
       
    def tick(self):
        # Generate a random points
        p1 = [random.randrange(0, self.cube.size) for _ in range(3)]
        # Gen a radius:
        r = random.randrange(0, self.cube.size//2)
        # Pick a random color
        color = cubehelper.color_plasma(self.progress)
        self.progress = self.progress + 0.3
        # Fill in all points on line with color
        for p in self.cube_points(p1, r):
            self.cube.set_pixel(p, color)
        pass
        
    def cube_points(self, center, radius):
        for x in range(-radius, radius+1):
            for y in range(-radius, radius+1):
                for z in range(-radius, radius+1):
                    result = (center[0]+x, center[1]+y, center[2]+z)
                    if (self.cube.size > result[0] and result[0] > 0 and 
                        self.cube.size > result[1] and result[2] > 0 and 
                        self.cube.size > result[2] and result[2] > 0):
                        yield result