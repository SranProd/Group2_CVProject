import os
import time
import csv
import random
import pyautogui
from pynput import mouse

output_dir = os.path.join(os.getcwd(), 'bot_datasets')
os.makedirs(output_dir, exist_ok=True)

filename = os.path.join(output_dir, f"bot_data_{int(time.time())}.csv")
data = [["timestamp", "state", "x", "y"]]
start_time = time.time()

def on_move(x, y):
    t = time.time() - start_time
    data.append([t, "Move", int(x), int(y)])

def on_click(x, y, button, pressed):
    t = time.time() - start_time
    state = "Pressed" if pressed else "Released"
    data.append([t, state, int(x), int(y)])

print("Bot starting in 3 seconds... Do not touch the mouse!")
time.sleep(3)

mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
mouse_listener.start()

for _ in range(10):
    x = random.randint(200, 1000)
    y = random.randint(200, 800)
    
    pyautogui.moveTo(x, y, duration=0.0)
    pyautogui.click()
    time.sleep(0.2)
    
    pyautogui.dragTo(x + 300, y - 100, duration=0.2, button='left')
    time.sleep(0.5)

mouse_listener.stop()

with open(filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(data)

print(f"Bot finished! Saved {len(data)} rows to {filename}")