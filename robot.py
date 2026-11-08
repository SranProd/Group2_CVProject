
import math
import random
import sys
import time

import pyautogui
from PIL import ImageChops, ImageGrab
from pynput import keyboard

from browser import DATA, HERE, Session

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

# Global ESC key kill switch
STOP_BOT = False

def _on_press(key):
    global STOP_BOT
    if key == keyboard.Key.esc:
        STOP_BOT = True

keyboard.Listener(on_press=_on_press, daemon=True).start()

def check_stop():
    if STOP_BOT:
        raise pyautogui.FailSafeException

def safe_sleep(duration):
    end = time.perf_counter() + duration
    while time.perf_counter() < end:
        check_stop()
        time.sleep(min(0.02, max(0.0, end - time.perf_counter())))

# positions as fractions of the page (same as LAYOUT in collector.html)
START   = (0.50, 0.62)
# clickable items: (center, max x offset, max y offset) in pixels
ITEMS = {
    "brand":      ((0.10, 0.06), 25, 4),
    "work":       ((0.62, 0.06), 12, 4),
    "about":      ((0.70, 0.06), 12, 4),
    "resume":     ((0.79, 0.06), 14, 4),
    "contact":    ((0.89, 0.06), 16, 4),
    "pet":        ((0.29, 0.34), 120, 40),
    "cakery":     ((0.71, 0.34), 120, 40),
    "permit":     ((0.29, 0.62), 120, 40),
    "canvas":     ((0.71, 0.62), 120, 40),
    "styleguide": ((0.32, 0.945), 30, 8),
    "citation":   ((0.50, 0.945), 25, 8),
    "github":     ((0.68, 0.945), 25, 8),
}
N_CLICKS = 6
OK      = (0.50, 0.55)

RATE = 100      # mouse moves per second

# page position on screen (left, top, width, height), set in calibrate()
VIEW = (0, 0) + tuple(pyautogui.size())


def _pink_mask(img):
    # mask of pink pixels. uses a range because some screens show
    # #ff00ff a bit differently
    r, g, b = img.split()
    keep = lambda band, test: band.point(lambda v: 255 if test(v) else 0)
    mask = ImageChops.multiply(keep(r, lambda v: v >= 170), keep(b, lambda v: v >= 170))
    mask = ImageChops.multiply(mask, keep(g, lambda v: v <= 120))
    mask = ImageChops.multiply(mask, keep(ImageChops.subtract(r, g), lambda v: v >= 90))
    mask = ImageChops.multiply(mask, keep(ImageChops.subtract(b, g), lambda v: v >= 90))
    return mask


def calibrate(timeout=25):
    # look for the 2 pink corner squares to find where the page is on screen
    global VIEW
    sw, sh = pyautogui.size()
    end = time.time() + timeout
    img = None
    while time.time() < end:
        check_stop()
        img = ImageGrab.grab().convert("RGB")
        box = _pink_mask(img).getbbox()
        if box and box[2] - box[0] > 300 and box[3] - box[1] > 300:
            kx, ky = sw / img.width, sh / img.height     # screenshots on mac are 2x size
            VIEW = (box[0] * kx, box[1] * ky, (box[2] - box[0]) * kx, (box[3] - box[1]) * ky)
            return True
        safe_sleep(0.5)
    if img is not None:                                  # save screenshot for debugging
        img.save(HERE / "calibration_debug.png")
    VIEW = (0, 0, sw, sh)                                # if not found, assume full screen
    return False


def px(frac):
    return VIEW[0] + frac[0] * VIEW[2], VIEW[1] + frac[1] * VIEW[3]


def min_jerk(t):            # smooth slow-fast-slow speed (like a real hand)
    return 10 * t**3 - 15 * t**4 + 6 * t**5


def ease_in_out(t):
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def cubic(p0, p1, p2, p3, t):
    u = 1 - t
    return (u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
            u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1])


def play(points, duration):
    # move through the points with even timing
    dt = duration / max(1, len(points))
    nxt = time.perf_counter()
    for x, y in points:
        check_stop()
        pyautogui.moveTo(int(round(x)), int(round(y)))
        nxt += dt
        wait = nxt - time.perf_counter()
        if wait > 0:
            time.sleep(wait)


# path shapes for the bot. each returns (function from 0-1 to a point, length)
def line_path(p0, p1):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    return (lambda u: (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)), L


def manhattan_path(p0, p1):
    # L-shaped path: horizontal then vertical (or the other way around)
    corner = (p1[0], p0[1]) if random.random() < 0.5 else (p0[0], p1[1])
    f1, d1 = line_path(p0, corner)
    f2, d2 = line_path(corner, p1)
    total = (d1 + d2) or 1
    return (lambda u: f1(u * total / d1) if d1 and u * total <= d1 else f2((u * total - d1) / d2 if d2 else 1)), total


def arc_path(p0, p1, bulge):
    # perfectly smooth arc
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    c = ((p0[0] + p1[0]) / 2 - dy / L * L * bulge, (p0[1] + p1[1]) / 2 + dx / L * L * bulge)
    f = lambda u: ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * c[0] + u * u * p1[0],
                   (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * c[1] + u * u * p1[1])
    return f, L * (1 + 2.5 * bulge * bulge)


# speed patterns: speed for each step of the move
def speed_profile(kind, n):
    if kind == "constant":                       # same speed all the way
        return [1.0] * n
    if kind == "stepped":                        # suddenly speeds up / slows down
        cuts = sorted(random.sample(range(1, n), min(n - 1, random.randint(1, 3)))) + [n]
        out, start = [], 0
        for c in cuts:
            out += [random.choice([0.25, 0.5, 1, 2, 4])] * (c - start)
            start = c
        return out
    if kind == "accelerate":                     # steadily faster
        return [0.2 + i / n for i in range(n)]
    if kind == "decelerate":                     # steadily slower
        return [1.2 - i / n for i in range(n)]
    if kind == "triangle":                       # faster then slower
        return [0.1 + 1 - abs(2 * i / n - 1) for i in range(n)]
    raise ValueError(kind)


def play_path(path_fn, duration, profile, rate=None):
    # move along the path using one of the speed patterns
    rate = rate or RATE
    n = max(2, int(duration * rate))
    speeds = speed_profile(profile, n)
    total, acc, pts = sum(speeds), 0.0, []
    for v in speeds:
        acc += v
        pts.append(path_fn(acc / total))
    play(pts, duration)


EASY_STYLES = ["line", "teleport", "manhattan", "stepped", "stutter", "accelerate", "decelerate", "triangle"]


class Bot:
    def __init__(self, level):
        self.level = level
        # random settings for each session so the bot data has more variety
        self.speed = random.uniform(500, 3500) # pixels per second
        self.styles = random.sample(EASY_STYLES, random.randint(1, 3))
        self.pause = random.choice([0.0, 0.05, 0.2, 0.5, 1.0]) # same pause every time (easy)
        self.hold = random.choice([0.0, 0.02, 0.1]) # same click length every time (easy)
        self.stutter_rate = random.choice([8, 12, 20]) # moves per second for choppy movement

    # movement
    def curve(self, target, duration, bend, ease, tremor=0.0):
        p0 = pyautogui.position()
        dx, dy = target[0] - p0[0], target[1] - p0[1]
        dist = math.hypot(dx, dy) or 1
        ux, uy = dx / dist, dy / dist # direction
        nx, ny = -uy, ux # perpendicular
        b1, b2 = (bend() for _ in range(2))
        p1 = (p0[0] + ux * dist * 0.3 + nx * dist * b1, p0[1] + uy * dist * 0.3 + ny * dist * b1)
        p2 = (p0[0] + ux * dist * 0.7 + nx * dist * b2, p0[1] + uy * dist * 0.7 + ny * dist * b2)
        n = max(3, int(duration * RATE))
        pts = []
        for i in range(1, n + 1):
            x, y = cubic(p0, p1, p2, target, ease(i / n))
            if tremor and i < n:
                x += random.gauss(0, tremor); y += random.gauss(0, tremor)
            pts.append((x, y))
        play(pts, duration)

    def move_to(self, target):
        check_stop()
        p0 = pyautogui.position()
        dist = math.hypot(target[0] - p0[0], target[1] - p0[1])
        if self.level == "easy":
            # pick one of this session's styles
            style = random.choice(self.styles)
            dur = max(0.05, dist / self.speed)
            if style == "teleport": # jump to the target
                pyautogui.moveTo(int(target[0]), int(target[1]))
            elif style == "manhattan": # L-shaped path
                f, L = manhattan_path(p0, target)
                play_path(f, max(0.05, L / self.speed), "constant")
            elif style == "stutter": # choppy(teleporty?) straight line
                play_path(line_path(p0, target)[0], dur, "constant", rate=self.stutter_rate)
            elif style == "line": # normal straight line
                play_path(line_path(p0, target)[0], dur, "constant")
            else: # straight line with changing speed
                play_path(line_path(p0, target)[0], dur, style)
        elif self.level == "medium":
            r = random.random()
            if r < 0.10: # sometimes teleport
                pyautogui.moveTo(int(target[0]), int(target[1]))
            elif r < 0.35: # arc with speed changes
                f, L = arc_path(p0, target, random.choice([-1, 1]) * random.uniform(0.05, 0.3))
                play_path(f, random.uniform(0.25, 0.9), random.choice(["stepped", "triangle", "constant"]))
            else: # curve with smooth speed
                side = random.choice([-1, 1]) * random.uniform(0.05, 0.3)
                self.curve(target, random.uniform(0.3, 0.9), bend=lambda: side, ease=ease_in_out)
        else:
            # hard: longer moves take more time (Fitts' law), random curves,
            # some shaking, and sometimes overshoots then corrects
            dur = (0.2 + 0.12 * math.log2(dist / 40 + 1)) * random.uniform(0.85, 1.3)
            if dist > 150 and random.random() < 0.7:
                ux, uy = (target[0] - p0[0]) / dist, (target[1] - p0[1]) / dist
                over = dist * random.uniform(0.03, 0.09)
                aim = (target[0] + ux * over + random.gauss(0, 6), target[1] + uy * over + random.gauss(0, 6))
                self.curve(aim, dur * 0.85, bend=lambda: random.gauss(0, 0.12), ease=min_jerk, tremor=0.8)
                safe_sleep(random.uniform(0.03, 0.12))
                self.curve(target, random.uniform(0.12, 0.25), bend=lambda: random.gauss(0, 0.2), ease=min_jerk, tremor=0.5)
            else:
                self.curve(target, dur, bend=lambda: random.gauss(0, 0.12), ease=min_jerk, tremor=0.8)

    def aim(self, frac, sx, sy):
        # pick a point near the center of the target
        x, y = px(frac)
        if self.level == "easy":
            return x, y # easy always clicks the exact center
        clamp = lambda v, s: max(-s, min(s, v))
        return x + clamp(random.gauss(0, sx / 2.5), sx), y + clamp(random.gauss(0, sy / 2.5), sy)

    # clicking
    def click(self):
        check_stop()
        if self.level == "easy":
            pyautogui.mouseDown(); safe_sleep(self.hold); pyautogui.mouseUp()
            return
        safe_sleep(random.uniform(0.05, 0.3) if self.level == "medium" else random.uniform(0.08, 0.35))
        hold = random.uniform(0.06, 0.14) if self.level == "medium" else max(0.04, random.gauss(0.10, 0.025))
        pyautogui.mouseDown(); safe_sleep(hold); pyautogui.mouseUp()

    def go_click(self, frac, sx=20, sy=None):
        self.move_to(self.aim(frac, sx, sx if sy is None else sy))
        self.click()

    def think(self):
        # pause between clicks
        check_stop()
        if self.level == "easy":
            safe_sleep(self.pause)
        elif self.level == "medium":
            safe_sleep(random.uniform(0.2, 1.0))
        else:
            end = time.perf_counter() + random.uniform(0.3, 1.5)
            while time.perf_counter() < end: # small random movements while waiting
                check_stop()
                if random.random() < 0.3:
                    x, y = pyautogui.position()
                    self.curve((x + random.gauss(0, 15), y + random.gauss(0, 10)),
                               random.uniform(0.1, 0.3), bend=lambda: random.gauss(0, 0.2), ease=min_jerk, tremor=0.5)
                safe_sleep(random.uniform(0.05, 0.2))

    # one full session: start, 6 clicks, OK
    def run(self, order):
        self.go_click(START, 25, 8)
        for key in order:
            frac, sx, sy = ITEMS[key]
            self.think()
            self.go_click(frac, sx, sy)
        self.think()
        self.go_click(OK, 25, 8)


def run_session(level):
    # returns "saved", "missed" or "stop"
    # random 6 items, same as the page does for humans
    order = random.sample(list(ITEMS), N_CLICKS)
    s = Session(label="bot", level=level, extra={"order": ",".join(order)})
    time.sleep(1.0)
    try:
        if not calibrate(): # wait for the page to open
            print("  Couldn't find the pink corner markers - assuming the page fills the screen.")
            print("  (Saved what the robot saw as calibration_debug.png)")
        safe_sleep(2.0)
        pyautogui.click(*px((0.5, 0.9))) # click empty space so Chrome has focus (not recorded)
        # start from a random spot (recording only starts after Start is clicked)
        pyautogui.moveTo(*px((random.uniform(0.15, 0.85), random.uniform(0.15, 0.85))))
        Bot(level).run(order)
    except pyautogui.FailSafeException:
        s.close()
        print("Emergency stop (ESC or corner) - this session was not saved.")
        return "stop"
    f = s.wait_for_file(timeout=10)
    if not f:
        shot = HERE / f"missed_{level}_{time.strftime('%H%M%S')}.png"
        ImageGrab.grab().save(shot) # screenshot to check what went wrong
        s.close()
        print(f"  missed a click - not saved, trying again (screenshot: {shot.name})")
        return "missed"
    s.close()
    print(f"  saved {f.name}")
    return "saved"


LEVELS = {"e": "easy", "m": "medium", "h": "hard"}


def counts():
    out_dir = DATA / "bot"
    return {lv: len(list(out_dir.glob(f"bot_{lv}_*.json"))) for lv in LEVELS.values()}


def show_progress():
    c = counts()
    parts = [f"{lv} {c[lv]}" for lv in LEVELS.values()]
    print(f"Robot sessions so far: {', '.join(parts)}   (total {sum(c.values())})")


def one_session(level):
    global STOP_BOT
    STOP_BOT = False
    # record one session, try again up to 3 times if a click misses
    print(f"\n{level.upper()} session - starting in 3 seconds. Hands off the mouse! (Press ESC = emergency stop)")
    try:
        safe_sleep(3)
    except pyautogui.FailSafeException:
        print("Emergency stop before start.")
        return "stop"
    for attempt in range(3):
        result = run_session(level)
        if result != "missed":
            return result
    print("  Missed 3 times in a row - send the missed_*.png screenshots.")
    return "missed"


def main():
    # level given in the command, e.g. python robot.py hard
    if len(sys.argv) > 1:
        level = sys.argv[1].lower()
        level = LEVELS.get(level[:1], level)
        if level not in LEVELS.values():
            sys.exit("Usage: python robot.py            (asks which level)\n"
                     "       python robot.py easy|medium|hard")
        one_session(level)
        show_progress()
        return

    # otherwise ask for a level each time
    while True:
        print()
        show_progress()
        choice = input("Which level? [e = easy, m = medium, h = hard, q = quit]: ").strip().lower()
        if choice[:1] == "q":
            break
        if choice[:1] not in LEVELS:
            print("Please type e, m, h or q.")
            continue
        if one_session(LEVELS[choice[:1]]) == "stop":
            break
    print("Bye!!!:)")


if __name__ == "__main__":
    main()