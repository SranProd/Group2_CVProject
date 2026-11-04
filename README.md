# Human or Bot? — Data Collection

## Files (keep them all in one folder)

| File             | What it does                                                                                                                         |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| `collector.html` | The test webpage, built from the portfolio. It records mouse moves and clicks with JavaScript and saves each session as a JSON file. |
| `human.py`       | **Our own Human.** Opens the page full screen so you can do the task. Saves to `our_json_data/human/`.                               |
| `robot.py`       | **Our own Robot.** PyAutoGUI does the same task at 3 levels. Saves to `our_json_data/bot/`.                                          |
| `browser.py`     | Helper for both: opens Chrome/Edge in its own window, full screen, and puts files in the right folder.                               |
| `export_csv.py`  | Converts all sessions to CSV (`timestamp, state, x, y`), the same format as the online datasets.                                     |

## Setup (once)

```
pip install pyautogui
```

**Mac:** use `pip3 install pyautogui`, and type `python3` instead of `python` in every command below.
Then go to System Settings → Privacy & Security and turn on **Accessibility** and **Screen Recording** for VS Code (or Terminal). Quit it with Cmd+Q and reopen it.

You also need Google Chrome (on Windows, Edge works too).

Optional: copy your portfolio's `fonts/` and `img/` folders into this folder so the page uses the real fonts and card images. The recorded data is the same either way.

## The task

1. Click **Start**
2. Click the 6 highlighted items, one after another. **Each session picks 6 random items out of the 12 on the page** (4 cards, 5 menu items, 3 footer buttons) in a random order. Humans and the robot use the same random rule, so neither gets an easier route. The order used is saved in the file as `click_order`.
3. Click **OK**. The session is saved.

## Each teammate collects: 30 human + 30 robot sessions

## Record human sessions (goal: 30)

```
python human.py
```

One session at a time: do the clicks and click **OK**. The window closes, the file is saved to `our_json_data/human/`, and you'll see `Human sessions so far: 7/30`.
Press **Enter** for the next one, or type `q` to quit. You can stop and come back any time, because the count picks up where you left off.

Tips: use the mouse naturally and don't rush. Use the same input every time (mouse or trackpad), and pick the matching option on the start screen.

## Record robot sessions (goal: 10 easy + 10 medium + 10 hard = 30)

```
python robot.py
```

It shows your progress and asks which level to run:

```
Robot sessions so far: easy 3/10, medium 2/10, hard 0/10   (total 5/30)
Which level? [e = easy, m = medium, h = hard, q = quit]:
```

Type `e`, `m` or `h` and press Enter. It records **one** session, then asks again. Type `q` to quit.

Shortcut for a single session: `python robot.py easy` (or `medium` / `hard`).

- **Don't touch the mouse while it runs.** Your movement would be recorded as bot data.
- **Emergency stop:** move the mouse hard into a screen corner. That session isn't saved.
- If a click misses, that session isn't saved. The robot tries again by itself and saves a screenshot (`missed_....png`).

| Level  | How it moves                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| easy   | **Super robotic.** Each session picks its own mix of 1–3 styles: straight lines, **teleporting** (jumping straight to the target), L-shaped grid paths, **sudden speed-ups/slow-downs**, mechanical acceleration or deceleration, low-rate "stuttering" jumps. Each session also gets a fixed speed (500–3500 px/s), an identical pause before every click (0–1 s) and an identical click hold, and always clicks dead centre. |
| medium | Smooth curves with eased speed, perfect arcs with sudden speed changes, occasional teleport, random delays, slightly random click spots                                                                                                                                                                                                                                                                                        |
| hard   | Human-like: wobbly curves, speed depends on distance, hand tremor, overshoot + correction, idle drifting, uneven click timing                                                                                                                                                                                                                                                                                                  |

## Make the CSV files

```
python export_csv.py
```

Every session becomes a CSV in `data_csv/human/` or `data_csv/bot/`:

```
timestamp,state,x,y
59,Move,535,502
850,Pressed,702,388
941,Released,702,388
```

- `timestamp` = milliseconds since Start
- `state` = Move / Pressed / Released
- `x, y` = mouse position in pixels

The folder name is the label (human or bot). Run it again any time after recording more sessions.

## What's inside a session JSON file

```json
{
  "label": "human" | "bot",
  "level": null | "easy" | "medium" | "hard",
  "device": "mouse" | "trackpad" | "pyautogui",
  "click_order": ["resume", "pet", "github", "work", "canvas", "brand"],
  "viewport": {"w": 1920, "h": 1080},
  "duration_ms": 9234.5,
  "events": [
    {"t": 12.3,  "type": "move", "x": 640, "y": 400},
    {"t": 850.1, "type": "down", "x": 702, "y": 388, "button": 0},
    {"t": 941.7, "type": "up",   "x": 702, "y": 388, "button": 0},
    {"t": 300,   "type": "task", "name": "click_1_cakery_hit"}
  ]
}
```

- Use `viewport` to normalise x,y to 0–1 (screens are different sizes).
- `task` events mark progress (e.g. which click was hit). **Don't give them to the model as features.**

## Collecting from classmates later

Upload `collector.html` to your portfolio repo (and the `fonts/` and `img/` folders it uses). Then send people the link:
`https://jihyebook-star.github.io/<repo>/collector.html`
When they click OK, the file downloads to their Downloads folder, and they send you the JSON.

## If something goes wrong

- **`python: command not found` (Mac):** use `python3`.
- **Robot says "Couldn't find the page on screen":** the browser window was hidden or not open yet (on Mac: check Screen Recording permission). Close other full-screen apps and try again.
- **Robot says "missed a click":** it retries by itself. If it happens a lot, send the `missed_....png` screenshots. Turning on Windows **Do Not Disturb** stops notifications covering the page.
- **Windows display scaling (125%, 150%) is fine.** The robot finds the page by looking for two tiny pink squares in the page corners.
- **If you change any positions in `collector.html` (`LAYOUT`), change the same numbers in `ITEMS` at the top of `robot.py`.**
