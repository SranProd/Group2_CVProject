from ultralytics import YOLO

# 1. Load a small pretrained YOLO classification model
model = YOLO("yolov8n-cls.pt")

# 2. Training it on our split folder (yolo_split has train/ val/ test/)
model.train(
    data="yolo_split",     # your 60/20/20 folder
    epochs=30,
    imgsz=224,
    batch=32,
    lr0=0.001,
    optimizer="AdamW",
    seed=42,
    name="baseline_vinay",   # my name
    project="runs/classify",
    hsv_h=0.0, hsv_s=0.0, hsv_v=0.0,   # colour = speed, so don't change colours
    auto_augment=None,                  # same reason
    erasing=0.0,
)

# 3. Check accuracy on VAL only
metrics = model.val(data="yolo_split", split="val")
print("Validation accuracy:", metrics.top1)