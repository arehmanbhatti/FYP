"""
Day 2 - dataset quality check.
Per species: image count, corrupt files, low-resolution files, exact duplicates.
Writes data/dataset_quality.json and prints a summary table.

Usage:
    python scripts/check_dataset.py
"""

import hashlib
import json
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent / "data"
MIN_SIDE = 400  # px; smaller images are too weak for YOLO training


def main():
    report = {}
    print(f"{'species':16s} {'images':>6} {'corrupt':>8} {'low-res':>8} {'dupes':>6} {'median WxH':>12}")
    for sp_dir in sorted((ROOT / "dataset").iterdir()):
        if not sp_dir.is_dir():
            continue
        corrupt, lowres, sizes, seen, dupes = [], [], [], {}, []
        files = sorted(sp_dir.glob("*.jpg"))
        for f in files:
            digest = hashlib.md5(f.read_bytes()).hexdigest()
            if digest in seen:
                dupes.append(f.name)
                continue
            seen[digest] = f.name
            img = cv2.imread(str(f))
            if img is None:
                corrupt.append(f.name)
                continue
            h, w = img.shape[:2]
            sizes.append((w, h))
            if min(w, h) < MIN_SIDE:
                lowres.append(f.name)
        med = sorted(sizes)[len(sizes) // 2] if sizes else (0, 0)
        report[sp_dir.name] = {
            "images": len(files), "corrupt": corrupt,
            "low_res": lowres, "duplicates": dupes, "median_size": med,
        }
        print(f"{sp_dir.name:16s} {len(files):>6} {len(corrupt):>8} {len(lowres):>8} "
              f"{len(dupes):>6} {med[0]}x{med[1]:>5}")

    (ROOT / "dataset_quality.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
