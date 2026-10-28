"""
Day 5 - evaluate the fine-tuned species model and choose the confidence threshold.

On the held-out validation split (data/yolo_dataset/images/val):
  1. box-level precision / recall / F1 per confidence threshold
     (a prediction is correct if it has the right species and IoU >= 0.5 with
     an unmatched ground-truth box), to pick the operating threshold
  2. per-species precision / recall at the chosen threshold
  3. image-level "exact species" hit rate of the fine-tuned model vs the
     pretrained OIV7 model (Day 3 metric) on the same validation images

Caveat: validation boxes are pseudo-labels taken from the pretrained model
(scripts/build_yolo_dataset.py), and only photos where the pretrained model
already found the animal are in the split.

Usage:
    python scripts/day5_evaluate.py
"""

import sys
from collections import defaultdict
from pathlib import Path

from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_pretrained import EXPECTED, outcome  # noqa: E402

import json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "yolo_dataset"
MODEL = ROOT / "runs" / "species_v1" / "weights" / "best.pt"
OUT = ROOT / "data" / "results" / "day5_summary.md"
FLOOR = 0.05
THRESHOLDS = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70]
IOU = 0.5


def iou(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0


def load_gt(label_file):
    gt = []
    for line in label_file.read_text().split("\n"):
        if line.strip():
            c, x, y, w, h = map(float, line.split())
            gt.append((int(c), (x - w / 2, y - h / 2, x + w / 2, y + h / 2)))
    return gt


def match(preds, gt, t):
    """Count TP / FP / FN per class at threshold t (boxes normalised 0..1)."""
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    used = set()
    for c, conf, box in sorted((p for p in preds if p[1] >= t), key=lambda p: -p[1]):
        best, best_j = 0, None
        for j, (gc, gbox) in enumerate(gt):
            if j not in used and gc == c and iou(box, gbox) > best:
                best, best_j = iou(box, gbox), j
        if best >= IOU:
            used.add(best_j)
            tp[c] += 1
        else:
            fp[c] += 1
    for j, (gc, _) in enumerate(gt):
        if j not in used:
            fn[gc] += 1
    return tp, fp, fn


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    return p, r, (2 * p * r / (p + r) if p + r else 0)


def main():
    model = YOLO(str(MODEL))
    names = model.names
    images = sorted((DATA / "images" / "val").glob("*.jpg"))
    preds, gts = {}, {}
    for r in model.predict(source=[str(f) for f in images], conf=FLOOR, imgsz=320, stream=True, verbose=False):
        stem = Path(r.path).stem
        preds[stem] = [(int(b.cls[0]), float(b.conf[0]), tuple(b.xyxyn[0].tolist())) for b in r.boxes]
        gts[stem] = load_gt(DATA / "labels" / "val" / f"{stem}.txt")

    # 1. threshold sweep
    lines = [f"## Fine-tuned model on the validation split ({len(images)} images, "
             f"{sum(len(g) for g in gts.values())} boxes)\n",
             "### Box-level precision / recall vs confidence threshold (IoU >= 0.5)\n",
             "| conf | precision | recall | F1 |", "|---|---|---|---|"]
    best_t, best_f1 = None, -1
    for t in THRESHOLDS:
        TP = FP = FN = 0
        for s in preds:
            tp, fp, fn = match(preds[s], gts[s], t)
            TP, FP, FN = TP + sum(tp.values()), FP + sum(fp.values()), FN + sum(fn.values())
        p, r, f1 = prf(TP, FP, FN)
        if f1 > best_f1:
            best_t, best_f1 = t, f1
        lines.append(f"| {t:.2f} | {p:.2f} | {r:.2f} | {f1:.2f} |")
    lines.append(f"\nBest F1 at conf = **{best_t:.2f}** -> chosen operating threshold.\n")

    # 2. per species at the chosen threshold
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    for s in preds:
        a, b, c = match(preds[s], gts[s], best_t)
        for k in names:
            tp[k] += a[k]
            fp[k] += b[k]
            fn[k] += c[k]
    lines += [f"### Per species at conf = {best_t:.2f}\n",
              "| Species | GT boxes | precision | recall | F1 |", "|---|---|---|---|---|"]
    for k, sp in names.items():
        p, r, f1 = prf(tp[k], fp[k], fn[k])
        lines.append(f"| {sp} | {tp[k] + fn[k]} | {p:.2f} | {r:.2f} | {f1:.2f} |")

    # 3. same images, Day 3 metric: does the image get its own species label?
    day3 = json.loads((ROOT / "data" / "results" / "day3_detections.json").read_text())
    lines += ["\n### Exact species hit rate on the same validation images (conf >= 0.25)\n",
              "| Species | images | pretrained OIV7 (Day 3) | fine-tuned |", "|---|---|---|---|"]
    tot = [0, 0, 0]
    for k, sp in names.items():
        stems = [s for s in preds if s.startswith(sp + "_")]
        pre = sum(outcome(sp, day3[f"{sp}/{s}.jpg"], 0.25) == "exact" for s in stems)
        fine = sum(any(c == k and conf >= 0.25 for c, conf, _ in preds[s]) for s in stems)
        tot = [tot[0] + len(stems), tot[1] + pre, tot[2] + fine]
        lines.append(f"| {sp} | {len(stems)} | {pre} ({100 * pre / len(stems):.0f}%) | "
                     f"{fine} ({100 * fine / len(stems):.0f}%) |")
    lines.append(f"| **all** | {tot[0]} | {tot[1]} ({100 * tot[1] / tot[0]:.0f}%) | "
                 f"{tot[2]} ({100 * tot[2] / tot[0]:.0f}%) |")

    text = "\n".join(lines)
    OUT.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
