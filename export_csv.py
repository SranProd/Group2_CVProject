# """
# Converts every recorded session (JSON) into a CSV with the same columns
# as the online mouse datasets:

#     timestamp,state,x,y
#     0,Move,640,400
#     16,Move,645,402
#     850,Pressed,702,388
#     941,Released,702,388

#   timestamp = milliseconds since the session started
#   state     = Move / Pressed / Released
#   x, y      = mouse position in pixels

# Run:
#     python export_csv.py

# Reads:  our_json_data/human/*.json  and  our_json_data/bot/*.json
# Writes: data_csv/human/*.csv  and  data_csv/bot/*.csv   (same file names)
# Running it again is safe - it just rewrites the CSVs.
# """
# import csv
# import json
# from pathlib import Path

# HERE = Path(__file__).resolve().parent
# SRC = HERE / "our_json_data"
# DST = HERE / "data_csv"

# STATE = {"move": "Move", "down": "Pressed", "up": "Released"}


# def convert(json_path, csv_path):
#     session = json.loads(json_path.read_text(encoding="utf-8"))
#     rows = 0
#     with open(csv_path, "w", newline="") as f:
#         w = csv.writer(f)
#         w.writerow(["timestamp", "state", "x", "y"])
#         for e in session["events"]:
#             if e["type"] in STATE:                       # skip scroll/task markers
#                 w.writerow([round(e["t"]), STATE[e["type"]], e["x"], e["y"]])
#                 rows += 1
#     return rows


# def main():
#     total = 0
#     for label in ("human", "bot"):
#         files = sorted((SRC / label).glob("*.json"))
#         if not files:
#             print(f"No files in our_json_data/{label}/")
#             continue
#         (DST / label).mkdir(parents=True, exist_ok=True)
#         for jp in files:
#             rows = convert(jp, DST / label / (jp.stem + ".csv"))
#             print(f"{label}/{jp.stem}.csv  ({rows} rows)")
#             total += 1
#     print(f"\nDone: {total} CSV files in {DST}")


# if __name__ == "__main__":
#     main()