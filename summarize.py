import csv, glob, os
import yaml
from collections import defaultdict

ROOT = "runs/classify/runs_sweep"
rows = []

for d in sorted(glob.glob(f"{ROOT}/*/")):
    res = os.path.join(d, "results.csv")
    if not os.path.exists(res):
        continue
    data = [{k.strip(): v.strip() for k, v in r.items()} for r in csv.DictReader(open(res))]
    if not data:
        continue

    acc_key = next(k for k in data[0] if "accuracy_top1" in k)
    loss_key = next(k for k in data[0] if k.startswith("train/loss"))
    vloss_key = next((k for k in data[0] if k.startswith("val/loss")), None)

    best = max(data, key=lambda r: float(r[acc_key]))
    args = {}
    a = os.path.join(d, "args.yaml")
    if os.path.exists(a):
        args = yaml.safe_load(open(a))

    name = os.path.basename(d.rstrip("/"))
    rows.append({
        "run": name,
        "config": name.rsplit("_s", 1)[0],
        "seed": args.get("seed"),
        "model": args.get("model"),
        "imgsz": args.get("imgsz"),
        "optimizer": args.get("optimizer"),
        "dropout": args.get("dropout"),
        "weight_decay": args.get("weight_decay"),
        "cos_lr": args.get("cos_lr"),
        "scale": args.get("scale"),
        "erasing": args.get("erasing"),
        "freeze": args.get("freeze"),
        "epochs_run": len(data),
        "best_epoch": best["epoch"],
        "best_val_acc": round(float(best[acc_key]), 4),
        "final_val_acc": round(float(data[-1][acc_key]), 4),
        "final_train_loss": round(float(data[-1][loss_key]), 4),
        "final_val_loss": round(float(data[-1][vloss_key]), 4) if vloss_key else "",
        "minutes": round(float(data[-1].get("time", 0)) / 60, 1),
    })

with open("run_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print(f"{'run':<22}{'best_acc':>9}{'best_ep':>8}{'epochs':>7}{'min':>6}")
for r in rows:
    print(f"{r['run']:<22}{r['best_val_acc']:>9.4f}{r['best_epoch']:>8}{r['epochs_run']:>7}{r['minutes']:>6}")

by = defaultdict(list)
for r in rows:
    by[r["config"]].append(r["best_val_acc"])
print("\nMean per config:")
for c, v in sorted(by.items(), key=lambda kv: -sum(kv[1]) / len(kv[1])):
    print(f"{c:<20} mean={sum(v)/len(v):.4f}  min={min(v):.4f}  max={max(v):.4f}  (n={len(v)})")
print("\nSaved run_summary.csv")