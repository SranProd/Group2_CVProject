import csv
from ultralytics import YOLO

DATA = "yolo_split"
DEVICE = "mps"            # or "cpu"

# Settings shared by every run (kept from train.py)
BASE = dict(
    data=DATA, epochs=40, patience=8, batch=16, imgsz=512, device=DEVICE,
    project="runs_sweep",
    fliplr=0.0, flipud=0.0, hsv_h=0.0, hsv_s=0.0, hsv_v=0.0,
    scale=0.0, erasing=0.0, auto_augment=None,
)

# Each entry only lists what it changes vs. BASE. "model" picks the weights.
CONFIGS = {
    "baseline":      dict(model="yolo11n-cls.pt"),
    "small_model":   dict(model="yolo11s-cls.pt"),
    "adamw_1e-3":    dict(model="yolo11n-cls.pt", optimizer="AdamW", lr0=0.001),
    "adamw_3e-4":    dict(model="yolo11n-cls.pt", optimizer="AdamW", lr0=0.0003),
    "dropout_0.3":   dict(model="yolo11n-cls.pt", dropout=0.3),
    "wd_5e-4_cos":   dict(model="yolo11n-cls.pt", weight_decay=0.0005, cos_lr=True),
    "mild_aug":      dict(model="yolo11n-cls.pt", scale=0.1, erasing=0.1),
    "imgsz_384":     dict(model="yolo11n-cls.pt", imgsz=384),
    "freeze_10":     dict(model="yolo11n-cls.pt", freeze=10),
}
SEEDS = [0, 1]   # run each config more than once; single runs are noisy

def main():
    rows = []
    for name, overrides in CONFIGS.items():
        accs = []
        for seed in SEEDS:
            cfg = {**BASE, **overrides}
            weights = cfg.pop("model")
            run_name = f"{name}_s{seed}"
            model = YOLO(weights)
            model.train(name=run_name, seed=seed, exist_ok=True, **cfg)
            best = YOLO(model.trainer.best)
            val_acc = best.val(data=DATA, split="val", imgsz=cfg["imgsz"],
                               device=DEVICE, verbose=False).top1
            accs.append(val_acc)
            print(f">>> {run_name}: val top1 = {val_acc:.4f}")
        mean = sum(accs) / len(accs)
        rows.append({"config": name, "mean_val_acc": round(mean, 4),
                     "min": round(min(accs), 4), "max": round(max(accs), 4)})

    rows.sort(key=lambda r: r["mean_val_acc"], reverse=True)
    with open("sweep_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    print("\nRanked by mean validation accuracy:")
    for r in rows:
        print(f"{r['config']:<14} mean={r['mean_val_acc']:.4f}  "
              f"range=[{r['min']:.4f}, {r['max']:.4f}]")

if __name__ == "__main__":
    main()