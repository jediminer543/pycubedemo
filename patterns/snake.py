import pygame
import cubehelper
import random
import math
import json
import sys
import time
import pickle
import os
import traceback

from SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
FPS = 30
SZ = 8

dirs = [
    (-1,0,0), # left
    ( 1,0,0), # right
    ( 0,1,0), # up
    (0,-1,0), # down
    ( 0,0,1), # forward
    (0,0,-1), # backward
    ]

colors = [
#    (0,160,0), # green
#    (192,0,0), # red
#    (0,64,255), # blue
#    (128,128,0), # yellow
#    (128,0,255), # violet
    (0,255,0), # green
    (255,0,0), # red
    (0,0,255), # blue
    (255,255,0), # yellow
    (128,0,255), # violet
]    

names = [
    "GREEN",
    "RED",
    "BLUE",
    "YELLOW",
    "VIOLET",
    ]
grid = [ None ] * 512
nplayers = 5
players = [ None ] * nplayers
startuptime = 30*FPS # frames
gamelength = 728.24 # seconds
#gamelength = 17 # seconds
starttime = None
gameended = False

plcols = []
for i in range(nplayers):
    plcols.append({'colname':names[i],'col':("#%02x%02x%02x" % colors[i])})

class hisc:
    score = 0
    name = None
    time = 0
    col = None

def savehi():
    try:
        file = open("snakehisc", "wb")
        obj = {'score': hisc.score, 'name': hisc.name, 'time': hisc.time, 'col': hisc.col}
        pickle.dump(obj, file, -1)
    except:
        print ("couldn't save hi score")

def loadhi():
    try:
        file = open("snakehisc", "rb")
        obj = pickle.load(file)
        hisc.score = obj['score']
        hisc.name = obj['name']
        hisc.time = obj['time']
        hisc.col = obj['col']
        print ("loaded hisc ",hisc)
    except:
        print ("couldn't load hi score")
    
wrap = True
targets = []
BLACK = (0,0,0)
WHITE = (255,255,255)
socket_to_player = {}
socket_to_socket = {}

def broadcast(o):
    #print ("broadcast ",len(socket_to_socket),o)
    for i in socket_to_socket:
        ws = socket_to_socket[i]
        assert(ws)
        #print ("trying to broadcast message to ",socket_to_player[i])
        ws.send(o)
        #print ("broadcast message",o," to ",ws)
        #     #except:
        #     #    print "failed"

def sendhi(p):
    t = time.strftime("%-2I:%M %p",time.localtime(hisc.time))
    o = {'type':'hisc','score':hisc.score,'name':hisc.name,'time':t,'col':hisc.col}
    if p:
        p.send(o)
    else:
        broadcast(o)
        savehi()
    
loadhi()

class Server(WebSocket):
    def send(self,o):
        #self.sendMessage(unicode(json.dumps(o)));
        self.sendMessage(json.dumps(o));
    def handleMessage(self):
        try:
            msg = json.loads(self.data)
            #print self.address, msg
            try:
                player = socket_to_player[self.address]
            except KeyError:
                player = None

            if 'player' in msg:
                player = int(msg['player'])
                socket_to_player[self.address] = player
                print ("setting player to %d" % player)
                if not players[player]:
                    players[player] = Player(player)
                    players[player].ws = self
                #self.send({'colname':names[player],'col':("#%02x%02x%02x" % players[player].col)})
                self.send({'colname':names[player],'col':("#%02x%02x%02x" % players[player].col)})
            elif 'key' in msg:
                assert(player is not None)
                key = int(msg['key'])
                assert (key>=0 and key<=5)
                print ("%d pressed key %d" % \
                    (player, int(msg['key'])))
                # as a courtesy prevent players reversing into themselves
                if tuple(map(sum,zip(dirs[players[player].dir],dirs[key]))) != (0,0,0):
                    players[player].dir = key
            elif 'hisc' in msg:
                print ("got hisc",msg)
                if int(msg['hisc']) == hisc.score:
                    if len(msg['hiscname']):
                        hisc.name = msg['hiscname'] # fixme: escaping
                        hisc.col = players[player].col
                        sendhi(None)
        except:
            traceback.print_exc()
            raise
        
    def handleConnected(self):
        try:
            print(self.address, 'connected')
            socket_to_socket[self.address] = self
            self.send({'type':'players','players':plcols})
            sendhi(self)
        except:
            traceback.print_exc()
            raise


    def handleClose(self):
        print(self.address, 'closed')
        s = socket_to_socket[self.address]
        assert(s)
        del socket_to_socket[s]
        try:
            pl = socket_to_player[self.address]
            #assert(pl.socket == self)
            del socket_to_player[self.address]
            pl.ws = None
        except:
            pass
        
server = SimpleWebSocketServer('', 27681, Server, selectInterval=1e-6)





pygame.init()
pygame.mixer.init()
pygame.mixer.set_num_channels(24)

## self.sample_plays = 0.0 # number of sample plays available
SOUNDDIR="patterns/snake-data/"
diesound = pygame.mixer.Sound(SOUNDDIR+"Hero_Death_00.wav")
eatsound = pygame.mixer.Sound(SOUNDDIR+"frog407.2.wav")
music = pygame.mixer.Sound(SOUNDDIR+"maggie3.wav")

def move(pos,dir):
    #print("pos",pos)
    newpos = list(map(sum,zip(pos,dirs[dir])))
    #print("newpos",newpos)
    for i in range(3):
        if newpos[i] < 0 or newpos[i] >= SZ:
            if wrap:
                newpos[i] %= SZ
            else:
                return None
    return tuple(newpos)

def get(pos):
    return grid[pos[0]+SZ*(pos[1]+SZ*pos[2])]

def set(pos,obj):
    grid[pos[0]+SZ*(pos[1]+SZ*pos[2])] = obj
    
def spawn():
    while True:
            pos0 = random.randrange(0,8)
            pos1 = random.randrange(0,8)
            pos2 = random.randrange(0,8)
            if get((pos0,pos1,pos2)):
                continue
            if not wrap:
                # bias spawning towards the centre
                sz2 = (SZ/2)-0.5
                sz22 = (SZ/2)+0.5
                c0 = pos0-sz2
                c1 = pos1-sz2
                c2 = pos2-sz2
                dist = (c0*c0+c1*c1+c2*c2)/sz22/sz22
                if dist>1 and random.random()*dist>1: # CHECKME
                    print ("bad: %d %d %d %f" % (pos0,pos1,pos2,dist))
                    continue
            return (pos0,pos1,pos2)

def plasma(val):
    val = int((val * 255)%255)
    if val < 85:
        r = val * 3;
        g = 255 - r;
        b = 0;
    elif val < 170:
        b = (val - 85) * 3;
        r = 255 - b;
        g = 0;
    else:
        g = (val - 170) * 3;
        b = 255 - g;
        r = 0;
    return (r, g, b)
       
class Player():
    speed = 12 # ticks per move
    cells = []
    col = None
    score = 0
    maxlen = 3 # max initial length
    dir = 1 # index into dirs array
    respawn_delay = 5 * FPS
    flashtime = 0.1*FPS
    dyingtime = 1.0*FPS
    ready_delay = 3.0 * FPS
    # player states
    state = None
    READY = 0
    ALIVE = 1
    DYING = 2
    DEAD  = 3
    alive_since = None
    
    # death reasons
    dead = False
    HIT_EDGE = 1
    HIT_WALL = 2
    HIT_SELF = 3
    HIT_OTHER_PLAYER = 4
    HIT_SELF_IDLE = 5

    ws = None # socket connection
    index = 0
    def __init__(self,i):
        self.index = i
        self.col = colors[self.index]
        self.state = self.DEAD
        self.ticksleft = self.respawn_delay

    def spawn(self):
        print ("spawning")
        for c in self.cells:
            set(c,None)
        for x in range(8):
            for y in range(8):
                for z in range(8):
                    if get((x,y,z))==self:
                        print ("%d %d %d" % (x,y,z))
                        assert(False)
        self.state = self.READY
        self.cells = [spawn()]
        self.dir = 1
        self.speed = 15
        self.score = 0
        self.ticksleft = self.ready_delay
        for c in self.cells:
            set(c,self)
        broadcast({'type':'spawn','player':self.index})
        
    def tick(self):
        if self.state != self.ALIVE:
            if self.state == self.DYING:
                self.ticksleft -= 1
                if self.ticksleft<0:
                    self.state = self.DEAD
                    self.ticksleft = self.respawn_delay
                    for c in self.cells:
                        set(c,None)
                return
            if self.state == self.READY:
                self.ticksleft -= 1
                if self.ticksleft<0:
                    self.state = self.ALIVE
                    self.alive_since = time.time()
                    self.ticksleft = 0
                return
            if self.state == self.DEAD:
                if self.ws:
                    self.ticksleft -= 1
                    if self.ticksleft<0:
                        self.spawn()
                else:
                    print ("no socket")
                return
                
        
        self.ticksleft -= 1
        #print "ticksleft %d" % self.ticksleft
        if self.ticksleft>0:
            return
        self.ticksleft += self.speed
        head = self.cells[0]
        newhead = move(head,self.dir)
        #print "newhead",newhead
        #print "len",len(self.cells)
        eaten = False
        dead = False
        
        if not newhead:
            print ("hit edge")
            dead = self.HIT_EDGE
        else:
            obj = get(newhead)
            typ = type(obj)
            #print obj, typ
            if isinstance(obj, Player):
                print ("hit player")
                if obj == self:
                    if len(self.cells)==8:
                        dead = self.HIT_SELF_IDLE
                    else:
                        dead = self.HIT_SELF
                else:
                    dead = self.HIT_OTHER_PLAYER
            elif isinstance(obj,Target):
                print ("yum")
                #os.system("aplay ~/mush2.wav&")
                eatsound.play()
                eaten = True
                self.score += 1
                self.ws.send({'score':self.score})
                self.speed *= 0.93 # FIXME
            
        if dead:
            # insert death sfx here
            #os.system("aplay ~/die.wav&")
            #diesound.play()
            #self.ws.send({'dead':dead})
            self.state = self.DYING
            self.ticksleft = self.dyingtime
            #if self.ws:
            broadcast({'type':"dead",'player':self.index,'reason':dead})
            if self.score > hisc.score:
                print ("new hi score ",self.score)
                hisc.score = self.score
                hisc.name = None
                hisc.time = time.time()
                self.ws.send({'type':'gothi','score':hisc.score})
                broadcast({'type':'newhi','player':self.index})
                sendhi(None)
            return

        set(newhead, self)

        if eaten or len(self.cells) < self.maxlen:
            # grow
            self.cells = [newhead] + self.cells
        else:
            # erase tail
            tail = self.cells[-1]
            #print ("tail",tail)
            set(tail, None)
            self.cells = [newhead] + self.cells[:-1]

    def color(self,x,y,z):
        if self.state==self.ALIVE or self.state==self.READY:
            # head should be brighter
            # if self.cells[0] == (x,y,z):
            #     return cubehelper.mix_color(self.col,WHITE,0.25)
            # else:
            #     return self.col
            if self.cells[0] == (x,y,z):
                return self.col
            else:
                #return cubehelper.mix_color(cubehelper.mix_color(self.col,BLACK,0.5),WHITE,0.5)
                return cubehelper.mix_color(self.col,BLACK,0.35)
        elif self.state == self.DYING:
            if self.respawn_delay-self.ticksleft<self.flashtime:
                return WHITE # flash at moment of impact
            # fade for 1 sec
            mix = self.ticksleft / self.dyingtime
            #print ("mix=%f" % mix)
            #if mix > 1: mix = 1
            return cubehelper.mix_color(BLACK,self.col,mix)
        else: # dead
            assert(self.state == self.DEAD)
            return BLACK

class Target():
    #color1 = (255,128,0)
    #color2 = (255,255,128)
    color1 = (64,64,64)
    color2 = (255,255,255)
    spawn_delay = 0.5*FPS
    spawn_timer = 0
    animtime = 0.4*FPS # pulse time
    growtime = 1.0 * FPS # fade in time after spawning
    def __init__(self):
        self.spawn()
    def spawn(self):
            self.pos = spawn()
            set(self.pos,self)
            self.ticks = 0
        
    def tick(self):
        #print ("target tick")
        if get(self.pos)!=self:
            # we were eaten
            # insert eaten sfx here
            self.spawn()
            
        self.ticks += 1
        if self.ticks >= self.growtime + self.animtime:
            self.ticks -= self.animtime
        
    def color(self,x,y,z):
        if self.ticks < self.growtime:
            return cubehelper.mix_color(BLACK,self.color1,self.ticks/self.growtime)
        else:
            t = (2.0*(self.ticks-self.growtime) / self.animtime)-1
            mix = (1-t*t)**3
            #print ("mix %f %f" % (t,mix))
            return cubehelper.mix_color(BLACK,plasma(self.ticks/self.animtime),mix)
            #return cubehelper.mix_color(self.color1,self.color2,mix)
        mix = self.ticks/self.growtime
        if mix>1: mix=1
        return cubehelper.mix_color(BLACK,plasma(self.ticks/self.animtime),mix)
    
class Pattern(object):
    def init(self):
        assert (SZ == self.cube.size)
        self.double_buffer = True
        #p = Player()
        #players.append(p)
        t = Target()
        targets.append(t)
        t = Target()
        targets.append(t)
        t = Target()
        targets.append(t)
        self.frame = 0
        return 1.0/FPS
    def tick(self):
        global starttime,gameended
        server.serveonce()
        self.cube.clear()
        self.frame += 1
        if self.frame < startuptime:
            return
        elif self.frame == startuptime:
            music.set_volume(0.15)
            music.play()
            starttime = time.time()
            print ("starttime=",starttime)

        if time.time() > starttime + gamelength + 10:
            exit(0)
        elif time.time() > starttime + gamelength:
            if not gameended:
                broadcast({'type':'exiting'})
                gameended = True
            print("game ended")
            return

        for p in players:
            if p:
                p.tick()
        for t in targets:
            t.tick()
        if self.frame % FPS == 0:
            s = []
            for i in range(nplayers):
                pl = players[i]
                if pl:
                    obj = {'score':pl.score,'state':pl.state }
                    if pl.state == pl.ALIVE:
                        obj['for'] = int(time.time()-pl.alive_since)
                    s.append(obj)
                else:
                    s.append(None)
            broadcast({'type':'scores', 'players':s})
        for x in range(0, SZ):
            for y in range(0, SZ):
                for z in range(0, SZ):
                    p = grid[x+SZ*(y+SZ*z)]
                    if p:
                        self.cube.set_pixel((x,y,z), p.color(x,y,z))
                    else:
                        self.cube.set_pixel((x,y,z), BLACK)

                        
                        #raise StopIteration
