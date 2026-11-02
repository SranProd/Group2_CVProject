import pandas as pd
import numpy as np
import cv2
import math
import os
import uuid

# Define where the YOLO images will be saved
YOLO_HUMAN_DIR = "yolo_dataset/human"
YOLO_BOT_DIR = "yolo_dataset/bot"
os.makedirs(YOLO_HUMAN_DIR, exist_ok=True)
os.makedirs(YOLO_BOT_DIR, exist_ok=True)

def draw_trajectory(csv_path, output_name, is_delbot=False):
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    if is_delbot:
        df = pd.read_csv(csv_path, skiprows=1, names=["timestamp", "state", "x", "y"])
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

def process_all_csvs(source_dir, dest_dir, is_delbot=False):
    if not os.path.exists(source_dir):
        print(f"Skipping {source_dir} (Not found)")
        return
        
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith(".csv") or file.endswith(".txt"):
                csv_path = os.path.join(root, file)
                unique_name = str(uuid.uuid4())[:8] + ".jpg"
                output_path = os.path.join(dest_dir, unique_name)
                draw_trajectory(csv_path, output_path, is_delbot)

print("Processing Human data...")
process_all_csvs("raw_csv_data/raw_human/SapiMouse_Humans", YOLO_HUMAN_DIR, is_delbot=False)
process_all_csvs("raw_csv_data/raw_human/MouseDynamics_Humans", YOLO_HUMAN_DIR, is_delbot=False)
process_all_csvs("raw_csv_data/raw_human/Delbot_Humans", YOLO_HUMAN_DIR, is_delbot=True)

print("Processing Bot data...")
process_all_csvs("raw_csv_data/raw_bot/Delbot_Bots", YOLO_BOT_DIR, is_delbot=True)
print("Done!")