"""
Day 5 - build a YOLO-format training set from the Day 2 images.

Following the base paper (Velpula et al. 2026, YOLOv12 + YAMNet), the visual
model is fine-tuned on our own species classes. The Day 2 photos only carry a
whole-image species label, so bounding boxes are pseudo-labelled from the
Day 3 pretrained detections:
  - a box is kept if its OIV7 class is the species' own class, a plausible
    related class, or the generic Animal / Mammal (e.g. Cheetah on a leopard
    photo becomes a 'leopard' box), at conf >= BOX_CONF
  - images marked E in the Day 3 review (no live animal) are dropped
  - images with no usable box are dropped (they would teach "no animal here")

The boxes are not hand-checked yet; review them in Roboflow before the final
training run.

Output: data/yolo_dataset/{images,labels}/{train,val}/ and data.yaml
(80/20 split per species, fixed seed).

Usage:
    python scripts/build_yolo_dataset.py
"""

import json
import random
import shutil
import sys
from collections import Counter
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from day3_adjusted import LABELS  # noqa: E402
from evaluate_pretrained import ANIMALS, EXPECTED, GENERIC  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "data"
OUT = ROOT / "yolo_dataset"
BOX_CONF = 0.25
VAL_SHARE = 0.2
SEED = 42
CLASSES = list(EXPECTED)  # class id = position in this list


def main():
    dets = json.loads((ROOT / "results" / "day3_detections.json").read_text())
    review = json.loads((ROOT / "results" / "day3" / "review_items.json").read_text())
    no_animal = {k for k, lab in zip(review, LABELS) if lab == "E"}

    if OUT.exists():
        shutil.rmtree(OUT)
    for split in ("train", "val"):
        (OUT / "images" / split).mkdir(parents=True)
        (OUT / "labels" / split).mkdir(parents=True)

    rng = random.Random(SEED)
    stats = {}
    for cid, sp in enumerate(CLASSES):
        _, family = EXPECTED[sp]
        usable = {}
        for key in sorted(k for k in dets if k.startswith(sp + "/")):
            if key in no_animal:
                continue
            boxes = [d["box"] for d in dets[key]
                     if d["conf"] >= BOX_CONF and d["cls"] in ANIMALS and d["cls"] in family | GENERIC]
            if boxes:
                usable[key] = boxes
        keys = list(usable)
        rng.shuffle(keys)
        n_val = round(len(keys) * VAL_SHARE)
        split_of = {k: ("val" if i < n_val else "train") for i, k in enumerate(keys)}

        for key, boxes in usable.items():
            src = ROOT / "dataset" / key
            h, w = cv2.imread(str(src)).shape[:2]
            lines = []
            for x1, y1, x2, y2 in boxes:
                x1, x2 = max(0, x1), min(w, x2)
                y1, y2 = max(0, y1), min(h, y2)
                lines.append(f"{cid} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} "
                             f"{(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}")
            split = split_of[key]
            shutil.copy(src, OUT / "images" / split / src.name)
            (OUT / "labels" / split / (src.stem + ".txt")).write_text("\n".join(lines) + "\n")

        c = Counter(split_of.values())
        stats[sp] = (sum(k.startswith(sp + "/") for k in dets), len(usable), c["train"], c["val"])

    names = "\n".join(f"  {i}: {sp}" for i, sp in enumerate(CLASSES))
    (OUT / "data.yaml").write_text(f"path: {OUT.as_posix()}\ntrain: images/train\nval: images/val\n"
                                   f"names:\n{names}\n")

    print("| Species | photos | with usable box | train | val |\n|---|---|---|---|---|")
    for sp, (n, u, tr, va) in stats.items():
        print(f"| {sp} | {n} | {u} | {tr} | {va} |")
    print(f"\nWritten to {OUT}")


if __name__ == "__main__":
    main()
