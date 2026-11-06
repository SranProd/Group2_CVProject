"""
Train a YOLO classification model to tell human vs bot mouse-path images apart.

Trains on DATA/train and checks accuracy on DATA/val (DATA is set below).
The test set is NOT used here (the group runs the final test together).

    python train_model.py

Change the settings below to try different hyperparameters. Each run gets
its own folder in runs/classify/, named after its settings, e.g.
    runs/classify/yolo11n_ep10_b16_lr0.01/
        weights/best.pt   best model (highest val accuracy) -> use for testing
        weights/last.pt   model from the last epoch -> for resuming training
        results.png       accuracy / loss graphs
"""
from ultralytics import YOLO

# ---- settings to try ----
MODEL = "yolo11n-cls.pt"   # n = nano (fastest). also try yolo11s-cls.pt (bigger)
EPOCHS = 10
BATCH = 16
LR0 = 0.01                # starting learning rate
PATIENCE = 5              # stop early if val accuracy stops improving
IMGSZ = 640                # our images are 640x640
DATA = "yolo_split"

run_name = f"{MODEL.split('-')[0]}_ep{EPOCHS}_b{BATCH}_lr{LR0}"

model = YOLO(MODEL)        # downloads automatically the first time
model.train(
    data=DATA,
    epochs=EPOCHS,
    batch=BATCH,
    lr0=LR0,
    optimizer="AdamW",     # set so lr0 is actually used
    patience=PATIENCE,
    imgsz=IMGSZ,
    hsv_h=0.0,             # no color changes: color = speed in our images
    hsv_s=0.0,
    hsv_v=0.0,
    scale=0.0,             # no random crops: the model always sees the whole path
    erasing=0.0,           # no random blacked-out patches (could hide the clues)
    name=run_name,
)

# accuracy of the best model on the validation set
best_path = model.trainer.best
metrics = YOLO(best_path).val(data=DATA, split="val", imgsz=IMGSZ,
                              name=run_name + "_val")

print(f"\nRun: {run_name}")
print(f"Val accuracy: {metrics.top1 * 100:.1f}%")
print(f"Best model:   {best_path}")