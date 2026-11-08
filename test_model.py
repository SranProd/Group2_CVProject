from pathlib import Path
from ultralytics import YOLO

RUNS_DIR = str(Path(__file__).resolve().parent / "runs")

if __name__ == "__main__":
    # Final score on the test images, only run once at the end
    model = YOLO("best_model.pt")

    metrics = model.val(
        data="yolo_split",
        split="test",
        imgsz=640,
        project=RUNS_DIR,
        name="final_test",
    )

    print("Test accuracy:", metrics.top1)