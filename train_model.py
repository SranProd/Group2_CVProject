from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO("yolo26n-cls.pt")

    model.train(
        data="yolo_split",
        epochs=50,
        patience=10,
        imgsz=640,
        batch=16,
        device="mps",
        name="baseline",
        # Turned off so the model sees the drawings exactly as they are
        auto_augment=None,
        hsv_h=0.0, hsv_s=0.0, hsv_v=0.0,
        fliplr=0.0,
        scale=0.0,
        erasing=0.0,
    )

    metrics = model.val(split="val", device="mps")
    print("Validation accuracy:", metrics.top1)
