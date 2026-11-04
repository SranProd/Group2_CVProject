import csv
import sys
import time
import pyautogui
from pynput import keyboard

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0

stop = False

def on_press(key):
    global stop
    if key == keyboard.Key.esc:
        stop = True
        return False

def load(path="human_movement.csv"):
    occurence = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            occurence.append({
                "type": row["type"],
                "t": float(row["t"]),
                "x": int(float(row["x"])),
                "y": int(float(row["y"])),
                "button": row["button"],
                "pressed": row["pressed"] == "True",
                "dy": int(float(row["dy"])) if row["dy"] else 0,
            })
    return occurence

def replay(events):
    t0 = time.perf_counter()
    for e in events:
        if stop:
            break
        wait = e["t"] - (time.perf_counter() - t0)
        if wait > 0:
            time.sleep(wait)

        if e["type"] == "move":
            pyautogui.moveTo(e["x"], e["y"])
        elif e["type"] == "click":
            pyautogui.moveTo(e["x"], e["y"])
            if e["pressed"]:
                pyautogui.mouseDown(button=e["button"])
            else:
                pyautogui.mouseUp(button=e["button"])
        elif e["type"] == "scroll":
            pyautogui.scroll(e["dy"])

def robot_style(events, step_seconds=0.5):
    targets = [(e["x"], e["y"]) for e in events if e["type"] == "click" and e["pressed"]]

    if not targets:
        moves = [e for e in events if e["type"] == "move"]
        targets = [(moves[0]["x"], moves[0]["y"]), (moves[-1]["x"], moves[-1]["y"])]
    for x, y in targets:
        if stop:
            break
        pyautogui.moveTo(x, y, duration=step_seconds, tween=pyautogui.linear)
        pyautogui.click()
        time.sleep(0.2)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "robot"
    events = load()
    keyboard.Listener(on_press=on_press).start()
    print("Starting in 3 seconds... (ESC or a screen corner aborts)")
    time.sleep(3)
    replay(events) if mode == "replay" else robot_style(events)
    print("Done.")