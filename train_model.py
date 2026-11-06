from pathlib import Path
from ultralytics import YOLO

RUNS_DIR = str(Path(__file__).resolve().parent / "runs")
RUN_NAME = "adamw_lr_0.0003_seed_1"  # Titles of each run

if __name__ == "__main__":
    model = YOLO("yolo26n-cls.pt")

    metrics = model.train(
        data="yolo_split",
        epochs=50,
        patience=10,
        imgsz=640,
        optimizer="AdamW", lr0=0.0003,
        seed=1,
        batch=16,
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
