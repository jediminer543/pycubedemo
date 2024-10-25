import random
import cubehelper
import os
import math
import pygame

# at start make stars fade up to maxnumstars fade down to minnumstars, at end fade up to maxnumstars end 130ish with fade down, flicker sun when stoppped, stars fade up/down vol/bright start and end, rain, distant thunder, cloundsend/forest/nightsfx transistion, more lightnngsfx
DT = 1.0 / 20
SPEED = 1.5
SUN_UP = 15
BIRDS_START = SUN_UP + 10.0 
STARS_END = BIRDS_START + 4.25 
#SUN is risen by 23.0
#BIGWIND_START = 50
CLOUD_START = SUN_UP + 33.0
WIND_START = CLOUD_START - 0.5
RAIN_START = CLOUD_START + 10.0
GREY_START = RAIN_START + 8.0
LIGHTNING_START = GREY_START + 6.0
STORM_END = LIGHTNING_START + 27.0
CLOUD_END = STORM_END + 5.0
FOREST_START = CLOUD_END
SUN_DOWN = CLOUD_END + 5.5
NIGHTSFX_START = SUN_DOWN + 8.0
NIGHT_START = SUN_DOWN + 22.5
END_ALL = 140.0
print(SUN_DOWN)

LIGHTNING_STICK_TICKS = int(0.3 / DT)

def loadsounds(dirname, namelist):
    sounds = []
    for name in namelist:
        newsound = pygame.mixer.Sound(dirname + name + '.wav')
        sounds.append(newsound)
    return sounds

GREY = 0x3D352A

class Star(object):

    def __init__(self, pos):
        self.x = pos[0]
        self.y = pos[1]
        self.speed = random.uniform(0.5, 6)
        self.maxtint = random.uniform(0.0,1)
        self.brightness = 0
        self.tintval = 0

    def isat(self, pos):
        return self.x == pos[0] and self.y == pos[1]

    def tick(self):
            self.brightness += int(self.speed * DT * 255)
            self.tintval = int(self.brightness * self.maxtint)
            if self.brightness > 255:
                self.speed = -self.speed
                self.brightness = 255
            return self.brightness >= 0
            # return self.brightness


class Sun(object):

    def __init__(self, cube):
        self.cube = cube
        self.center = [-7, 3.5, -7]

    def draw(self, brightness):
        for y in range(0, self.cube.size):
            for x in range(0, self.cube.size):
                for z in range(0, self.cube.size):
                        dist = self.distance(x, y, z)                        
                        if dist > 3:
                            continue
                        colour = self.colour(dist)
                        fade = brightness
                        if dist > 2:
                            fade *= (3 - dist)
                        colour = cubehelper.mix_color(0, colour, fade)
                        self.cube.set_pixel((x, y, z), colour)

    def move(self, up, down, brightness):
        sunspeed = DT/2.5
        if brightness == 0.0:
            self.center[0] = -1
        if up and self.center[2] < 8:
            self.center[0] += sunspeed
            self.center[2] += sunspeed
        if down:
            self.center[0] += sunspeed
            self.center[2] -= sunspeed

    def distance(self, x, y, z):
        return math.sqrt( math.pow(x-self.center[0], 2) + math.pow(y-self.center[1], 2) + math.pow(z-self.center[2], 2))

    def colour(self, distance):
        return cubehelper.mix_color((255, 0, 0), (255, 100, 0), max((distance - 0.5), 0)/2.5)

class Drop(object):
    def __init__(self, cube, cloud):
        self.cube = cube
        self.x = clip(int(cloud[0]), 0, 7)
        self.y = clip(int(cloud[1]), 0, 7)
        self.z = 5.0
        self.speed = random.uniform(4.0, 8.0) * DT
        self.color = 0x000080
    
    def tick(self):
        z0 = int(math.floor(self.z))
        self.cube.set_pixel((self.x , self.y, z0), self.color)
        self.z -= self.speed

def clip(x, a, b):
    if x < a:
        return a
    if x > b:
        return b
    return x

class Pattern(object):

    def init(self):
        pygame.init()
        pygame.mixer.init( )
        pygame.mixer.set_num_channels(24)
        self.rainsfx = loadsounds('patterns/weathermatt-data/stormsfx/rainsfx/', ['rain%d' %n for n in range(8)])
        self.lightningsfx = loadsounds('patterns/weathermatt-data/lightningsfx/', ['lightning%d' %n for n in range(4)])
        self.starssfx = loadsounds('patterns/weathermatt-data/starssfx/', ['plinks%d' %n for n in range(20)])
        self.birds = pygame.mixer.Sound('patterns/weathermatt-data/morningsfx/birds.wav')
        self.wind = pygame.mixer.Sound('patterns/weathermatt-data/stormsfx/wind1.wav')
        self.bigwind = pygame.mixer.Sound('patterns/weathermatt-data/stormsfx/bigwind.wav')
        self.forest = pygame.mixer.Sound('patterns/weathermatt-data/forestnightsfx/forest.wav')
        self.nightsfx = pygame.mixer.Sound('patterns/weathermatt-data/forestnightsfx/nightsfx.wav')
        self.sun = Sun(self.cube)
        self.double_buffer = True
        self.clouds = []        
        self.rain = []
        self.lpos = []
        self.stars = []
        self.star_counter = 0.0
        self.lz = None
        self.ly = None
        self.lx = None
        self.birdsplayed = False
        self.windplayed = False
        self.windfade = False
        self.bigwindplayed = False
        self.forestplayed = False
        self.nightsfxplayed = False
        self.timer = 0.0
        return DT

    def tick(self):
        self.cube.clear()
        self.timer += DT
        print(int(self.timer))

        if self.birdsplayed == False and self.timer >= BIRDS_START:
            self.birds.play()
            self.birdsplayed = True
        if self.timer > WIND_START:
            pygame.mixer.Sound.fadeout(self.birds, 6000)
        if self.windplayed == False and self.timer >= WIND_START:
            pygame.mixer.Sound.set_volume(self.wind, 0.5)
            self.wind.play()
            self.windplayed = True
        if self.timer > CLOUD_END - 3.0:
            pygame.mixer.Sound.fadeout(self.wind, 6000)
        if self.forestplayed == False and self.timer >= FOREST_START:
            self.forest.play()
            self.forestplayed = True
        if self.timer > NIGHTSFX_START:
            pygame.mixer.Sound.fadeout(self.forest, 10000)
        if self.nightsfxplayed == False and self.timer >= NIGHTSFX_START:
            self.nightsfx.play()
            self.nightsfxplayed = True
        if self.timer > 150.0:
            pygame.mixer.Sound.fadeout(self.nightsfx, 10000)
        # if self.bigwindplayed == False and self.timer >= BIGWIND_START:
        #     self.bigwind.play()
        #     self.bigwindplayed = True

        if self.timer > CLOUD_START and self.timer < CLOUD_END and \
                ((len(self.clouds) == 0) or (random.uniform(0.0, 0.90/SPEED) < DT)):
            newcloud = [-1.0, random.uniform(0, 7), random.uniform(5, 7)]
            self.clouds.append(newcloud)
        
        if self.timer > STORM_END + 2.0:
            sunbright = 1.0
        elif self.timer > STORM_END:
            sunbright = (self.timer - STORM_END) / 2.0
        elif self.timer > GREY_START + 2.0:
            sunbright = 0.0
        elif self.timer > GREY_START:
            sunbright = (GREY_START + 2.0 - self.timer) / 2.0
        else:
            sunbright = 1.0
        cloudcolor = cubehelper.mix_color( GREY, 0xFFFFFF, sunbright)
        
        if self.timer > RAIN_START and self.timer < STORM_END + 2.0:
            if random.uniform(0.0, 0.05) < DT * 5:
                cloud = random.choice(self.clouds)
                self.rain.append(Drop(self.cube, cloud))

        if self.timer < STARS_END or self.timer > NIGHT_START:
            self.star_counter += DT * 20
            while self.star_counter > 1.0:
                self.star_counter -= 1.0
                testcoords = (random.randint(0,7), random.randint(0,7))
                if all( not star.isat(testcoords) for star in self.stars):
                    self.stars.append(Star(testcoords))

        if len(self.lpos) == 0:
            if self.timer > LIGHTNING_START and self.timer < STORM_END - 2.0 and \
                    random.uniform(0.0, 1.0) < 0.1:
                cloud = random.choice(self.clouds)
                self.lx = clip(int(cloud[0]), 0, 7)
                self.ly = clip(int(cloud[1]), 0, 7)
                self.lz = 5
            else:
                self.lz = -LIGHTNING_STICK_TICKS
        else:
            self.lz -= 1
            self.lx = clip(self.lx + random.randint(-1, 1), 0, 7)
            self.ly = clip(self.ly + random.randint(-1, 1), 0, 7)
        if self.lz < 0:
            if self.lz < -LIGHTNING_STICK_TICKS:
                self.lpos = []
        else:
            self.lpos.append((self.lx, self.ly, self.lz))

        self.sun.draw(sunbright)

        for x in range(self.cube.size):
            for y in range(7):
                for z in range(5,8):
                    bestdistance = 2.0
                    for cloud in self.clouds:
                        xdist = cloud[0] - x
                        ydist = cloud[1] - y
                        zdist = cloud[2] - z
                        dist = math.sqrt(xdist*xdist + ydist*ydist + zdist*zdist)
                        if dist < bestdistance:
                            bestdistance = dist
                    if bestdistance < 1:
                        color = cloudcolor
                        self.cube.set_pixel((x, y, z), color)
                    elif bestdistance < 1.5:
                        color = cubehelper.mix_color( cloudcolor, 0, (bestdistance - 1.0)*2)
                        self.cube.set_pixel((x, y, z), color)
        
        if self.timer > RAIN_START and self.timer < STORM_END:
            rain = self.rain
            self.rain = []
            for drop in rain:
                drop.tick()
                if drop.z >= 0:
                    self.rain.append(drop)
                elif random.uniform(0.0, 1.0) < 0.5:
                    thissound = random.choice(self.rainsfx)
                    pygame.mixer.Sound.set_volume(thissound, random.uniform(0.40, 0.80))
                    thissound.play()

        for pos in self.lpos:
            self.cube.set_pixel(pos, (255, 255, 0))
            if pos[2] == 0:
                thissound = random.choice(self.lightningsfx)
                pygame.mixer.Sound.set_volume(thissound, random.uniform(0.30, 0.50))
                thissound.play()

        self.sun.move(self.timer > SUN_UP and self.timer < SUN_DOWN, self.timer > SUN_DOWN, sunbright)
        
        old_stars = self.stars
        self.stars = []
        for star in old_stars:
            if (star.x < 0 or star.x > 7 or star.y < 0 or star.y > 7):
                continue
            self.cube.set_pixel((star.x, star.y, 7), (star.brightness, star.brightness, star.tintval))
            if star.tick():
                self.stars.append(star)
            elif random.uniform(0.0, 1.0) < .20:
                thissound = random.choice(self.starssfx)
                pygame.mixer.Sound.set_volume(thissound, random.uniform(0.10, 0.50))
                thissound.play()

        i = 0
        while i < len(self.clouds):
            x = self.clouds[i][0]
            x += DT * SPEED
            if x > 8.0:
                del self.clouds[i]
            else:
                self.clouds[i][0] = x
                i += 1


        if self.timer > 160.0:
            raise StopIteration
