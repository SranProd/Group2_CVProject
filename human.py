"""
Human data collection.
Opens the test page full screen, you click the 6 highlighted items and then OK.
Each session gets saved to our_json_data/human/.

    python human.py

Press Enter after each session to record another one, or q to quit.
"""
from browser import Session

while True:
    print("\nOpening the test page... click the 6 highlighted items, then OK button")
    s = Session(label="human")
    f = s.wait_for_file()
    s.close()
    if f:
        print(f"Saved {f.name}")
    else:
        print("Window was closed before OK - the data is not saved.")
    total = len(list(s.out_dir.glob("*.json")))
    print(f"Human sessions so far: {total}")
    if input("Record another? [Enter = yes, q = quit] ").strip().lower()[:1] in ("q", "n"):
        break
print("Bye!!!:)")