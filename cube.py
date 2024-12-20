#! /usr/bin/env python

# Framework for running LED cube demos
# Copyright (C) Paul Brook <paul@nowt.org>
# Released under the terms of the GNU General Public License version 3

import argparse
import itertools
import pkgutil
import time
import signal
import cubehelper
import random
import logging

def load_patterns(cube, match):
    patterns = {}
    arglist = {}
    if match is None:
        namelist = None
    else:
        namelist = []
        for name in match:
            if ':' in name:
                (name, arg) = name.split(':', 1)
            else:
                arg = None
            namelist.append(name)
            arglist[name] = arg
    for (finder, name, ispkg) in pkgutil.walk_packages(["patterns"]):
        if match is not None and name not in arglist:
            continue
        print("Loading pattern module '%s'" % name)
        try:
            loader = finder.find_module(name)
            mod = loader.load_module(name)
            constructor = mod.Pattern
        except Exception as e:
            print(e)
            print("Failed to load pattern '%s'" % name)
            constructor = None
        if constructor is not None:
            pobj = constructor()
            pobj.name = name
            pobj.cube = cube
            pobj.port = arglist.get("netport")
            pobj.arg = arglist.get(name)
            patterns[name] = pobj
    if len(patterns) == 0:
        raise Exception("No patterns found")
    if match is None:
        ordered = list(patterns.values())
        random.shuffle(ordered)
    else:
        ordered = map(lambda x: patterns[x], namelist)
    if args.noloop:
        return iter(ordered)
    else:
        return itertools.cycle(ordered)

# Returns true to quit
def run_pattern(cube, pattern):
    try:
        interval = pattern.init()
        try:
            db = pattern.double_buffer
        except:
            db = False
        now = time.time()
        next_tick = now + interval
        sec_tick = now + 1.0
        frames = 0
        if args.interval > 0:
            partial = now + args.interval * 0.5
            expires = now + args.interval
        else:
            partial = None
            expires = None
        print("Running pattern %s" % pattern.name)
        if db:
            cube.clear()
            cube.swap()
        else:
            cube.single_buffer()
            cube.clear()
        null_iteration = False
        while True:
            try:
                pattern.tick()
                null_iteration = False
            except StopIteration:
                if null_iteration:
                    raise
                null_iteration = True
            cube.render()
            if db:
                cube.swap()
            now = time.time()
            if expires is not None and now > expires:
                raise StopIteration
            if next_tick > now:
                time.sleep(next_tick - now)
            next_tick += interval
            frames += 1
            if now >= sec_tick:
                if debug_frames:
                    print("%d/%d" % (frames, int(1.0/interval)))
                sec_tick += 1.0
                frames = 0
    except StopIteration:
        return

def sigterm_handler(_signo, _stack_frame):
    raise KeyboardInterrupt

# Set up additional logging to the console
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(consoleHandler)

ap = argparse.ArgumentParser(description="LED cube demo program")
ap.add_argument('-P', '--port', type=str,
        help="Serial port")
ap.add_argument('-s', '--size', type=int, default=8,
        help="Cube size")
ap.add_argument('-p', '--pattern', type=str, action='append',
        help="Patterns to run")
ap.add_argument('-i', '--interval', type=float,
        help="Maximum interval between patterns")
ap.add_argument('-f', '--frames', action='store_true', default=False,
        help="Display framerate")
ap.add_argument('-n', '--noloop', action='store_true', default=False,
        help="Run selected pattern(s) only once, don't loop through them")
ap.add_argument('-N', '--netport', type=str,
        help="Network port for patterns")
ap.add_argument('-r', '--rotation', type=str,
        help="Rotation to apply to the cube in the format either just number of 90 degree rotations around z")
ap.add_argument('-F', '--flip', type=str,
        help="Flip a given axis of the cube, provide a string containing the axes to flip, i.e. xz")
args = ap.parse_args()

debug_frames = args.frames
if args.port is None:
    import glcube
    c = glcube.Cube(args)
else:
    import serialcube
    c = serialcube.Cube(args)

if args.rotation is not None:
    # EVIL PYTHON MAGIC
    set_pixel_old = c.set_pixel
    rotation_split = args.rotation.split(":")
    assert(len(rotation_split)==1 or len(rotation_split)==3)
    print("rot")
    if (int(args.rotation[0]) % 4 == 0):
        c.set_pixel = lambda xyz, rgb:  set_pixel_old((xyz[0], xyz[1], xyz[2]), rgb)
    if (int(args.rotation[0]) % 4 == 1):
        c.set_pixel = lambda xyz, rgb:  set_pixel_old((c.size-1-xyz[1], xyz[0], xyz[2]), rgb)
    if (int(args.rotation[0]) % 4 == 2):
        c.set_pixel = lambda xyz, rgb:  set_pixel_old((c.size-1-xyz[0], c.size-1-xyz[1], xyz[2]), rgb)
    if (int(args.rotation[0]) % 4 == 3):
        c.set_pixel = lambda xyz, rgb:  set_pixel_old((xyz[1], c.size-1-xyz[0], xyz[2]), rgb)

if args.flip is not None:
   set_pixel_old = c.set_pixel
   print("flip x {} y {} z {} ".format("x" in args.flip, "y" in args.flip, "z" in args.flip))
   c.set_pixel = lambda xyz, rgb: set_pixel_old((c.size-1-xyz[0] if "x" in args.flip else xyz[0], c.size-1-xyz[1] if "y" in args.flip else xyz[1], c.size-1-xyz[2] if "z" in args.flip else xyz[2]), rgb)

if c.color:
    c.plasma = cubehelper.color_plasma
else:
    c.plasma = cubehelper.mono_plasma

if args.pattern is None:
    pattern_list = None
else:
    pattern_list = ','.join(args.pattern).split(',')
if args.interval is None:
    if pattern_list is not None and len(pattern_list) == 1:
        args.interval = 0.0
    else:
        args.interval = 10.0

try:
    #c.set_brightness((8, 4, 4))
    #c.set_brightness((0xc0, 0xff, 0xff))
    #c.set_brightness((0x30, 0x45, 0x40))
    #c.set_brightness((0x10, 0x08, 0x08))
    pass
except:
    pass

signal.signal(signal.SIGTERM, sigterm_handler)

patterns = load_patterns(c, pattern_list)
try:
    for p in patterns:
        run_pattern(c, p)
except KeyboardInterrupt:
    pass
c.single_buffer()
c.clear()
c.render()
