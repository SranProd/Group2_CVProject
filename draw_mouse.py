import pandas as pd
import numpy as np
import cv2
import math
import os
import random
import shutil

random.seed(360)  # Same picks on everyone's computer

# Define where the YOLO images will be saved
YOLO_HUMAN_DIR = "yolo_dataset/human"
YOLO_BOT_DIR = "yolo_dataset/bot"
shutil.rmtree("yolo_dataset", ignore_errors=True)  # Start clean so re-runs don't pile up
os.makedirs(YOLO_HUMAN_DIR, exist_ok=True)
os.makedirs(YOLO_BOT_DIR, exist_ok=True)

def draw_trajectory(csv_path, output_name, is_delbot=False):
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    if is_delbot:
        with open(csv_path) as f:
            width, height = f.readline().strip().split(":")[1].split(",")
        df = pd.read_csv(csv_path, skiprows=1, names=["timestamp", "state", "x", "y"])
        # Some Delbot files save positions as 0-1 fractions of the screen
        if df["x"].max() <= 1 and df["y"].max() <= 1:
            df["x"] = df["x"] * float(width)
            df["y"] = df["y"] * float(height)
    else:
        df = pd.read_csv(csv_path)
        if "client timestamp" in df.columns:
            df["timestamp"] = df["client timestamp"]
            
    if df["timestamp"].diff().mean() > 1.0:
        df["timestamp"] = df["timestamp"] / 1000.0
        
    prev_x, prev_y, prev_t = None, None, None
    
    for index, row in df.iterrows():
        try:
            x = int(float(row['x']))
            y = int(float(row['y']))
            t = float(row['timestamp'])
            state = str(row['state'])
        except:
            continue 
            
        if "Pressed" in state or "Click" in state:
            cv2.circle(img, (x, y), radius=6, color=(0, 255, 255), thickness=-1)
            
        if prev_x is not None:
            distance = math.hypot(x - prev_x, y - prev_y)
            time_diff = t - prev_t
            if time_diff <= 0: time_diff = 0.001 
            speed = distance / time_diff
            
            if speed > 1500:     color = (0, 0, 255)   
            elif speed > 400:    color = (0, 255, 0)   
            else:                color = (255, 0, 0)   
                
            cv2.line(img, (prev_x, prev_y), (x, y), color, thickness=2)
            
        prev_x, prev_y, prev_t = x, y, t

    cv2.imwrite(output_name, img)

def list_csvs(source_dir):
    paths = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".csv") or file.endswith(".txt"):
                paths.append(os.path.join(root, file))
    if not paths:
        raise SystemExit(f"No data found in {source_dir}")
    return sorted(paths)  # Sorted so the seed picks the same files on every computer

def draw_all(csv_paths, source_dir, dest_dir, prefix, is_delbot=False):
    for csv_path in csv_paths:
        relative = os.path.splitext(os.path.relpath(csv_path, source_dir))[0]
        image_name = prefix + "_" + relative.replace(os.sep, "_") + ".jpg"
        draw_trajectory(csv_path, os.path.join(dest_dir, image_name), is_delbot)
    print(f"  {prefix:<16}{len(csv_paths):>5}")

def pick_evenly(groups, total):
    # Take the same amount from each group. A group with too few gives all it has,
    # and the bigger groups make up the difference.
    picks = {}
    for i, name in enumerate(sorted(groups, key=lambda g: len(groups[g]))):
        share = (total + len(groups) - i - 1) // (len(groups) - i)
        picks[name] = random.sample(groups[name], min(share, len(groups[name])))
        total -= len(picks[name])
    return picks

OUR_HUMANS = "our_collected_data/our_human_csvs"
OUR_BOTS = "our_collected_data/our_bot_csvs"
SAPI_HUMANS = "raw_csv_data/raw_human/SapiMouse_Humans"
DELBOT_HUMANS = "raw_csv_data/raw_human/Delbot_Humans"
DELBOT_BOTS = "raw_csv_data/raw_bot/Delbot_Bots"
DELBOT_BOT_TYPES = {
    "bot_gan": "circles_bot_gan",
    "bot_naturalmouse": "circles_bot_naturalmousemotion",
    "bot_pyhm": "circles_bot_pyhm",
    "bot_pynput": "circles_bot_pynput",
}

our_humans = list_csvs(OUR_HUMANS)
our_bots = list_csvs(OUR_BOTS)

print("Processing Human data...")
draw_all(our_humans, OUR_HUMANS, YOLO_HUMAN_DIR, "ours_human")
draw_all(list_csvs(SAPI_HUMANS), SAPI_HUMANS, YOLO_HUMAN_DIR, "sapi")
draw_all(list_csvs(DELBOT_HUMANS), DELBOT_HUMANS, YOLO_HUMAN_DIR, "delbot_human", is_delbot=True)
human_total = len(os.listdir(YOLO_HUMAN_DIR))

print("Processing Bot data...")
draw_all(our_bots, OUR_BOTS, YOLO_BOT_DIR, "ours_bot")  # Ours are always kept, only Delbot gets cut
groups = {prefix: list_csvs(os.path.join(DELBOT_BOTS, folder)) for prefix, folder in DELBOT_BOT_TYPES.items()}
picks = pick_evenly(groups, human_total - len(our_bots))
for prefix, csv_paths in picks.items():
    draw_all(csv_paths, os.path.join(DELBOT_BOTS, DELBOT_BOT_TYPES[prefix]), YOLO_BOT_DIR, prefix, is_delbot=True)

human_images = os.listdir(YOLO_HUMAN_DIR)
bot_images = os.listdir(YOLO_BOT_DIR)
ours_human_images = sum(name.startswith("ours_") for name in human_images)
ours_bot_images = sum(name.startswith("ours_") for name in bot_images)
print(f"Human images: {len(human_images)} ({ours_human_images} ours)")
print(f"Bot images:   {len(bot_images)} ({ours_bot_images} ours)")
if ours_human_images != len(our_humans) or ours_bot_images != len(our_bots):
    raise SystemExit("ERROR: some of our own sessions didn't make it into the dataset")
if len(human_images) != len(bot_images):
    raise SystemExit("ERROR: human and bot counts don't match")
print("Done!")
