"""
Day 5 - fine-tune YOLO on the 8 target species.

Training settings follow the base paper (Velpula et al. 2026): image size
320x320, batch size 16, 100 epochs, starting from pretrained weights
(transfer learning). The proposal names YOLOv11, so yolo11n.pt is the
default; pass --model yolo12n.pt to match the paper's YOLOv12 exactly.

Runs on CPU here (no GPU); use Google Colab for larger models / more data.

Usage:
    python scripts/train.py
    python scripts/train.py --model yolo12n.pt --name species_v12
"""

import argparse
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="yolo11n.pt", help="pretrained weights to start from")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--name", default="species_v1")
    parser.add_argument("--resume", action="store_true", help="continue an interrupted run from its last.pt")
    args = parser.parse_args()

    if args.resume:
        model = YOLO(str(ROOT / "runs" / args.name / "weights" / "last.pt"))
        model.train(resume=True)
        metrics = model.val()
        print(f"\nmAP@50 = {metrics.box.map50:.3f}   mAP@50-95 = {metrics.box.map:.3f}")
        return

    model = YOLO(args.model)
    model.train(
        data=str(ROOT / "data" / "yolo_dataset" / "data.yaml"),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=str(ROOT / "runs"),
        name=args.name,
        exist_ok=True,
        seed=42,
        workers=4,
        plots=True,
    )
    metrics = model.val()
    print(f"\nmAP@50 = {metrics.box.map50:.3f}   mAP@50-95 = {metrics.box.map:.3f}")
    print(f"Best weights: {ROOT / 'runs' / args.name / 'weights' / 'best.pt'}")


if __name__ == "__main__":
    main()
