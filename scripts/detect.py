"""
Day 1 - YOLO proof of concept
Runs a pretrained YOLO model on an image or video and saves the
annotated result with bounding boxes + class labels + confidence.

Usage:
    python scripts/detect.py --source data/sample_images/deer.jpg
    python scripts/detect.py --source data/sample_videos/forest.mp4
"""

import argparse
from pathlib import Path
from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="path to image or video")
    parser.add_argument(
        "--model",
        default="yolov8m-oiv7.pt",
        help="pretrained YOLO weights (yolov8m-oiv7.pt covers 601 classes incl. deer, leopard, tiger, fox, etc.)",
    )
    parser.add_argument("--conf", type=float, default=0.3, help="confidence threshold")
    args = parser.parse_args()

    model = YOLO(args.model)

    project_dir = Path(__file__).resolve().parent.parent / "data" / "results"

    results = model.predict(
        source=args.source,
        conf=args.conf,
        save=True,
        project=str(project_dir),
        name="run",
        exist_ok=True,
        agnostic_nms=True,
    )

    for r in results:
        print(f"\nFile: {r.path}")
        if len(r.boxes) == 0:
            print("  No objects detected.")
            continue
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            conf = float(box.conf[0])
            print(f"  {label:15s} confidence={conf:.2f}")

    print("\nAnnotated output saved in data/results/run/")


if __name__ == "__main__":
    main()
