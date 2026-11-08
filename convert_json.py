import os
import json
import csv

# Folders for our own collected data
OUR_HUMAN_CSV_DIR = "our_collected_data/our_human_csvs"
OUR_BOT_CSV_DIR = "our_collected_data/our_bot_csvs"

os.makedirs(OUR_HUMAN_CSV_DIR, exist_ok=True)
os.makedirs(OUR_BOT_CSV_DIR, exist_ok=True)

IGNORE_DIRS = {".git", ".vscode", "__pycache__", "yolo_dataset", "IAT360_Mouse"}

def convert_json_to_csv(json_path):
    file_name = os.path.basename(json_path)
    base_name = os.path.splitext(file_name)[0]
    file_lower = file_name.lower()

    if "medium" in file_lower:  # We only use easy and hard
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    if not isinstance(data, dict) or "events" not in data:
        return

    # Sort into human or bot by the start of the file name
    label = str(data.get("label", "")).lower()
    if file_lower.startswith("human"):
        output_dir = OUR_HUMAN_CSV_DIR
    elif file_lower.startswith("bot") or "bot" in label:
        output_dir = OUR_BOT_CSV_DIR
    else:
        return

    # Keep the exact original filename, just swapping .json for .csv
    csv_filename = os.path.join(output_dir, f"{base_name}.csv")
    rows = [["timestamp", "state", "x", "y"]]

    for event in data.get("events", []):
        if "x" not in event or "y" not in event:
            continue

        event_type = str(event.get("type", "")).lower()

        if event_type in ["move", "mousemove", "pointermove"]:
            state = "Move"
        elif event_type in ["click", "down", "mousedown", "pointerdown", "pressed"]:
            state = "Pressed"
        elif event_type in ["up", "mouseup", "pointerup", "released"]:
            state = "Released"
        else:
            continue

        t_seconds = float(event["t"]) / 1000.0
        x = int(round(float(event["x"])))
        y = int(round(float(event["y"])))

        rows.append([t_seconds, state, x, y])

    if len(rows) > 1:
        with open(csv_filename, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerows(rows)
        print(f"Converted: {file_name} -> {csv_filename} ({len(rows) - 1} rows)")

print("Scanning workspace for human and bot JSON files...")
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
    
    for file in files:
        if file.endswith(".json") and (file.lower().startswith("human") or file.lower().startswith("bot")):
            convert_json_to_csv(os.path.join(root, file))

print("Done!")