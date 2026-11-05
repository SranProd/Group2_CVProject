from ultralytics import YOLO

def main():
    model = YOLO("yolo11n-cls.pt")
    model.train(
        data="yolo_split",
        epochs=60,
        patience=15,
        imgsz=512,
        batch=16,
        device="mps",
        freeze=10,              # winner from the sweep
        project="runs_final",
        name="final_model",
        fliplr=0.0, flipud=0.0,
        hsv_h=0.0, hsv_s=0.0, hsv_v=0.0,
        scale=0.0, erasing=0.0,
        auto_augment=None,
    )
    print("Best weights:", model.trainer.best)

    best = YOLO(model.trainer.best)
    metrics = best.val(data="yolo_split", split="test", imgsz=512, device="mps")
    print("TEST top-1 accuracy:", metrics.top1)

if __name__ == "__main__":
    main()