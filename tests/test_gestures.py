#!/usr/bin/env python3
"""End-to-end test, no touchpad or hands needed: python3 tests/test_gestures.py

Creates a fake 5-finger touchpad (through /dev/uinput), runs a separate test
instance of five-finger-gestures on it with a test config whose actions just
append to a log file, plays scripted touches and checks which actions fired.
Your real touchpad and running copy are not touched. The fake touchpad (and
its pass-through copy) briefly appear as input devices while the test runs;
the touches are 5-finger ones held back from the desktop, plus a 4-finger tap
and a 4-finger swipe on the fake device.
"""
import fcntl, glob, os, struct, subprocess, sys, tempfile, time

PROG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "five-finger-gestures")
HERE = tempfile.mkdtemp(prefix="ffg-test-")
LOG, CONF = os.path.join(HERE, "actions.log"), os.path.join(HERE, "test.conf")
RES = 34
EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
BTN_LEFT, BTN_TOOL_FINGER, BTN_TOUCH = 0x110, 0x145, 0x14A
TOOLS = {1: 0x145, 2: 0x14D, 3: 0x14E, 4: 0x14F, 5: 0x148}
ABS_X, ABS_Y, SLOT, MX, MY, TID = 0, 1, 0x2F, 0x35, 0x36, 0x39
EV = struct.Struct("llHHi")


def ioc(d, t, nr, size):
    return (d << 30) | (size << 16) | (ord(t) << 8) | nr


def make_pad():
    ui = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
    for t in (EV_SYN, EV_KEY, EV_ABS):
        fcntl.ioctl(ui, ioc(1, "U", 100, 4), t)
    for k in [BTN_LEFT, BTN_TOUCH] + list(TOOLS.values()):
        fcntl.ioctl(ui, ioc(1, "U", 101, 4), k)
    for p in (0, 2):  # pointer, buttonpad
        fcntl.ioctl(ui, ioc(1, "U", 110, 4), p)
    for code, mx in ((ABS_X, 3839), (ABS_Y, 2647), (SLOT, 4), (MX, 3839), (MY, 2647), (TID, 65535)):
        fcntl.ioctl(ui, ioc(1, "U", 103, 4), code)
        res = RES if code in (ABS_X, ABS_Y, MX, MY) else 0
        fcntl.ioctl(ui, ioc(1, "U", 4, 28), struct.pack("=H2x6i", code, 0, 0, mx, 0, 0, res))
    fcntl.ioctl(ui, ioc(1, "U", 3, 92), struct.pack("=4H80sI", 0x18, 0xFF01, 0xFF02, 1, b"fft-sim touchpad", 0))
    fcntl.ioctl(ui, 0x5501)
    time.sleep(0.5)
    for d in glob.glob("/sys/class/input/event*/device/name"):
        if open(d).read().strip() == "fft-sim touchpad":
            return ui, "/dev/input/" + d.split("/")[4]
    raise SystemExit("fake pad not found")


class Hand:
    def __init__(self, ui):
        self.ui, self.next_id, self.pts = ui, 100, {}

    def frame(self, evs):
        os.write(self.ui, b"".join(EV.pack(0, 0, *e) for e in evs) + EV.pack(0, 0, EV_SYN, 0, 0))
        time.sleep(0.012)

    def keys(self, n):
        evs = [(EV_KEY, BTN_TOUCH, 1 if n else 0)]
        evs += [(EV_KEY, code, 1 if k == n else 0) for k, code in TOOLS.items()]
        return evs

    def down(self, n, x=60, y=40):
        evs = []
        for i in range(n):
            self.next_id += 1
            self.pts[i] = [x - 30 + 15 * i, y + (8 if i == 0 else 0)]  # mm; finger 0 = thumb
            evs += [(EV_ABS, SLOT, i), (EV_ABS, TID, self.next_id),
                    (EV_ABS, MX, int(self.pts[i][0] * RES)), (EV_ABS, MY, int(self.pts[i][1] * RES))]
        self.frame(evs + self.keys(n))

    def move(self, dx, dy, steps=12):
        for _ in range(steps):
            evs = []
            for i, p in self.pts.items():
                p[0] += dx / steps
                p[1] += dy / steps
                evs += [(EV_ABS, SLOT, i), (EV_ABS, MX, int(p[0] * RES)), (EV_ABS, MY, int(p[1] * RES))]
            self.frame(evs)

    def lift(self, slots=None):
        slots = list(self.pts) if slots is None else slots
        evs = []
        for i in slots:
            evs += [(EV_ABS, SLOT, i), (EV_ABS, TID, -1)]
            del self.pts[i]
        self.frame(evs + self.keys(len(self.pts)))


def write_conf(extra=""):
    act = lambda name: f'sh -c "echo {name} >> {LOG}"'
    with open(CONF, "w") as f:
        f.write(f"""slide up = {act('slide-up')}
slide down = {act('slide-down')}
swipe left = {act('swipe-left')}
swipe right = {act('swipe-right')}
tap = {act('tap')}
4-finger tap = {act('4tap')}
pinch out = {act('pinch-out')}
{extra}""")


def new_lines(seen):
    time.sleep(0.6)
    lines = open(LOG).read().split() if os.path.exists(LOG) else []
    return lines[seen:], len(lines)


def main():
    for f in (LOG,):
        if os.path.exists(f):
            os.remove(f)
    write_conf()
    ui, dev = make_pad()
    env = dict(os.environ, XDG_RUNTIME_DIR=HERE)
    daemon = subprocess.Popen([sys.executable, "-I", PROG, "--debug", "--config", CONF, "--device", dev],
                              env=env, stdout=open(os.path.join(HERE, "daemon.log"), "w"),
                              stderr=subprocess.STDOUT)
    time.sleep(1.2)
    h, seen, failures = Hand(ui), 0, 0

    def scenario(name, expect, steps):
        nonlocal seen, failures
        steps()
        got, seen = new_lines(seen)
        ok = got == expect
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}: expected {expect}, got {got}")

    def slide_up_30():
        h.down(5); h.move(0, -30); h.lift()
    scenario("slide up 30mm (step 7mm)", ["slide-up"] * 4, slide_up_30)

    def up_then_down():
        h.down(5); h.move(0, -22); h.move(0, 37); h.lift()
    scenario("slide up 22mm then down 37mm", ["slide-up"] * 3 + ["slide-down"] * 5, up_then_down)

    def swipe_right():
        h.down(5); h.move(15, 0); h.lift()
    scenario("swipe right 15mm", ["swipe-right"], swipe_right)

    def swipe_left_drop():
        h.down(5); h.move(-6, 0); h.lift([4]); h.move(-8, 0); h.lift()
    scenario("swipe left, a finger drops halfway", ["swipe-left"], swipe_left_drop)

    def slide_drop():
        h.down(5); h.move(0, -10); h.lift([3]); h.move(0, -15); h.lift()
    scenario("slide up 25mm, a finger drops halfway", ["slide-up"] * 3, slide_drop)

    def tap():
        h.down(5); time.sleep(0.1); h.lift()
    scenario("5-finger tap", ["tap"], tap)

    def long_press():
        h.down(5); time.sleep(0.6); h.lift()
    scenario("5-finger long press (not a tap)", [], long_press)

    def small_up():
        h.down(5); h.move(0, -5); h.lift()
    scenario("5mm up (too small for a slide or swipe)", [], small_up)

    def tap4():
        h.down(4); time.sleep(0.1); h.lift()
    scenario("4-finger tap", ["4tap"], tap4)

    def swipe4():
        h.down(4); h.move(20, 0); h.lift()
    scenario("4-finger swipe (left to the desktop)", [], swipe4)

    def pinch():
        h.down(5)
        for _ in range(10):
            evs = []
            for i, p in h.pts.items():
                p[0] += (p[0] - 60) * 0.06
                p[1] += (p[1] - 42) * 0.06
                evs += [(EV_ABS, SLOT, i), (EV_ABS, MX, int(p[0] * RES)), (EV_ABS, MY, int(p[1] * RES))]
            h.frame(evs)
        h.lift()
    scenario("5-finger spread (pinch out)", ["pinch-out"], pinch)

    write_conf("slide step = 10mm\ntap max time = 50ms\n")
    time.sleep(0.05)
    scenario("after config edit: slide step 10mm, slide up 30mm", ["slide-up"] * 3, slide_up_30)
    scenario("after config edit: tap max 50ms, 100ms tap", [], tap)

    daemon.terminate()
    daemon.wait()
    fcntl.ioctl(ui, 0x5502)
    os.close(ui)
    print(f"\n{failures} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
