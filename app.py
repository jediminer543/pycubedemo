from typing import Callable, Optional
from flask import Flask, render_template, request, logging as flask_logging, redirect, url_for
import pkgutil, json, threading, time, importlib, traceback
from serialcube import Cube as SerialCube
from glcube import Cube as GlCube
import cubehelper
from logging import Logger
import os.path

app = Flask(__name__)

app.config.from_prefixed_env(prefix='CUBECTL')

####
# Cube display thread
####
class CubeThread(threading.Thread):
    logger: Logger
    pattern_queue: list[str]
    is_repeat: bool
    cube: GlCube | SerialCube
    current_pattern: Optional[str]
    port: Optional[str]
    size: int
    interval: float
    netport: int
    debug_frames: bool
    pattern_args: dict[str, any]

    def __init__(self, config: dict, logger: Logger):
        super().__init__()
        self._stop_event = threading.Event()
        # setup auto-defaults
        self.is_repeat = True
        self.pattern_queue = list()
        # setup logging
        self.logger = logger
        # load config
        self.port = config["PORT"] if "PORT" in config else None
        self.interval = float(config["INTERVAL"]) if "INTERVAL" in config  else 10.0
        self.debug_frames = bool(config["DEBUG_FRAMES"]) if "DEBUG_FRAMES" in config else False
        self.size = int(config["SIZE"]) if "SIZE" in config else 8
        # TODO add config parse for these
        self.debug_frames = True
        self.pattern_args = dict()
        self.netport = 16080

    def stop(self) -> None:
        self._stop_event.set()

    def _stopped(self) -> bool:
        return self._stop_event.is_set()
    
    # class CubeArgs:
    #     port: Optional[str]
    #     size: int

    def setup(self) -> None:
        #args = {"port": self.port, "size": self.size} # type: ignore
        if self.port is None:
            c = GlCube(self)
        else:
            c = SerialCube(self)

        if c.color:
            c.plasma = cubehelper.color_plasma
        else:
            c.plasma = cubehelper.mono_plasma

        self.cube = c

    class Pattern:
        init: Callable[[], None]
        tick: Callable[[], None]
        cube: GlCube | SerialCube
        port: int
        arg: any



    def load_pattern(self, name: str) -> Optional[Pattern]:
        pattern = None
        try:
            #importlib.invalidate_caches()
            module = __import__("patterns."+name, globals=globals(), locals=locals(), level=0)
            #module = importlib.import_module(".patterns."+name, "pycubedemo")
            # module = None
            # for (finder, pname, ispkg) in pkgutil.walk_packages(["pycubedemo/patterns"]):
            #     if pname == name:
            #             print(pname)
            #         # try:
            #             loader = finder.find_module(pname)
            #             help(loader.exec_module)
            #             module = loader.load_module(pname)
            #         # except Exception as e:
            #         #     print(e)
            #         #     print("Failed to load pattern module'%s'" % name)
            #         #     constructor = None
            if module is None:
                print("Failed to load module")
                return None
            if "Pattern" in vars(vars(module)[name]):
                pattern = vars(module)[name].Pattern()
            else:
                print("Failed to find pattern loader")
                print(vars(vars(module)[name]))
        except Exception as e:
            #print(e)
            print(traceback.format_exc())
            print("Failed to load pattern '%s'" % name)
            return None
        if pattern:
            pattern.name = name
            pattern.cube = self.cube
            pattern.port = self.netport
            pattern.arg = self.pattern_args[name] if name in self.pattern_args else None
        return pattern
        

    def run_pattern(self, pattern: Pattern):
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
            if self.interval > 0:
                partial = now + self.interval * 0.5
                expires = now + self.interval
            else:
                partial = None
                expires = None
            print("Running pattern %s" % pattern.name)
            if db:
                self.cube.clear()
                self.cube.swap()
            else:
                self.cube.single_buffer()
                self.cube.clear()
            null_iteration = False
            while True:
                try:
                    pattern.tick()
                    null_iteration = False
                except StopIteration:
                    if null_iteration:
                        raise
                    null_iteration = True
                self.cube.render()
                if db:
                    self.cube.swap()
                now = time.time()
                if expires is not None and now > expires:
                    raise StopIteration
                if next_tick > now:
                    time.sleep(next_tick - now)
                next_tick += interval
                frames += 1
                if now >= sec_tick:
                    if self.debug_frames:
                        print("%d/%d" % (frames, int(1.0/interval)))
                    sec_tick += 1.0
                    frames = 0
        except StopIteration:
            return

    def run(self) -> None:
        self.setup()
        while not self._stopped():
            if (len(self.pattern_queue) > 0):
                try:
                    print("Selecting Pattern")
                    pattern_name = self.pattern_queue.pop(0)
                    if (self.is_repeat):
                        print("Requeueing pattern " + pattern_name)
                        self.pattern_queue.append(pattern_name)
                    print("Loading pattern " + pattern_name)
                    pattern_obj = self.load_pattern(pattern_name)
                    print("Attempting to run pattern " + pattern_name)
                    if pattern_obj:
                        print("Running pattern " + pattern_name)
                        self.current_pattern = pattern_name
                        self.run_pattern(pattern_obj)
                        self.current_pattern = None
                    else:
                        print("Removing pattern " + pattern_name)
                        self.pattern_queue.remove(pattern_name)
                except Exception as e: 
                    self.logger.error("Exception in logic",exc_info=e)
            else:
                self.cube.single_buffer()
                self.cube.clear()
                self.cube.render()
                #self.logger.info("Cube is idle")
        # teardown
        self.cube.single_buffer()
        self.cube.clear()
        self.cube.render()
        print("Render thread exit")

#####
# we are not running a database so lol
####
cubethread = CubeThread(app.config, flask_logging.create_logger(app))
cubethread.start()

# @app.teardown_appcontext
# def teardown_appthread(exception):
#     cubethread.stop()

##################
# route handlers #
##################

# list patterns
@app.route("/patterns/")
def patterns() -> str:
    return json.dumps([name for (finder, name, ispkg) in pkgutil.walk_packages(["pycubedemo/patterns"])])

# Queue up patterns
@app.route("/patterns/queue", methods=["GET","POST"])
def queue_patterns() -> str:
    if request.method == "GET":
        return {"queue": cubethread.pattern_queue, "repeat": cubethread.is_repeat}
    elif request.method == "POST":
        payload = request.json
        if isinstance(payload, str):
            cubethread.pattern_queue.append(payload)
            return {"queue": cubethread.pattern_queue, "repeat": cubethread.is_repeat}
        elif isinstance(payload, list):
            cubethread.pattern_queue.extend(payload)
            return {"queue": cubethread.pattern_queue, "repeat": cubethread.is_repeat}
        elif isinstance(payload, dict):
            if ("queue" in payload):
                cubethread.pattern_queue.extend(payload["queue"])
            if ("repeat" in payload):
                cubethread.is_repeat = bool(payload["repeat"])
            return {"queue": cubethread.pattern_queue, "repeat": cubethread.is_repeat}
    elif request.method == "DELETE":
        if isinstance(payload, str):
            cubethread.pattern_queue.remove(payload)
            return {"queue": cubethread.pattern_queue, "repeat": cubethread.is_repeat}
        elif isinstance(payload, list):
            # TODO check method
            for p in payload["queue"]:
                    cubethread.pattern_queue.remove(p)
            return {"queue": cubethread.pattern_queue, "repeat": cubethread.is_repeat}
        elif isinstance(payload, dict):
            if ("queue" in payload):
                for p in payload["queue"]:
                    cubethread.pattern_queue.remove(p)
            return {"queue": cubethread.pattern_queue, "repeat": cubethread.is_repeat}



@app.route("/config/")
def config() -> str:
    return json.dumps(list(app.config.keys()))

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name:str=None):
    return render_template('hello.html', name=name)

@app.route("/")
def frontend_redir():
    return  redirect(url_for("frontend"))

@app.route("/frontend")
def frontend():
    return render_template("frontend.html")

@app.route('/frontend/queue')
def queue():
    return render_template('queue.html', queue=cubethread.pattern_queue, repeat=cubethread.is_repeat)