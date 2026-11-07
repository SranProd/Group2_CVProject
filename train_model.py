from pathlib import Path
from ultralytics import YOLO

RUNS_DIR = str(Path(__file__).resolve().parent / "runs")
RUN_NAME = "dropout_0.1"  # Titles of each run

if __name__ == "__main__":
    model = YOLO("yolo26n-cls.pt")

    metrics = model.train(
        data="yolo_split",
        epochs=50,
        patience=10,
        imgsz=640,
        batch=16,
        dropout=0.1,
        device="mps",
        project=RUNS_DIR,
        name=RUN_NAME,
        # Turned off so the model sees the drawings exactly as they are (no images modified)
        auto_augment=None,
        hsv_h=0.0, hsv_s=0.0, hsv_v=0.0,
        fliplr=0.0,
        scale=0.0,
        erasing=0.0,
    )

    print("Validation accuracy:", metrics.top1)
