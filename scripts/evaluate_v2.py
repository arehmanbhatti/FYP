"""
Week 1 fixes - compare species models on the v2 held-out TEST split.

Week 1 (v1) was only measured on its own 63-image validation split. v2 has a
separate test split (15%) that is never used for training or for choosing the
threshold. Every model gets the same treatment:

  1. the confidence threshold is chosen on the v2 VALIDATION split (best box F1)
  2. at that threshold, on the TEST split:
     - mAP@50 and mAP@50-95 (Ultralytics), box precision / recall / F1, per species
     - exact-species hit rate per image (Day 3 / Day 5 metric)
     - false-alarm rate on negative images (confuser animals, empty scenes, people)
     - recall on synthetic night / IR versions of the test photos

Test images that were in the v1 training or validation set are left out, so v1
is not tested on photos it has already seen.

Caveat: test boxes are still automatic pseudo-labels (OIV7 + YOLO-World),
not hand-checked.

Usage:
    python scripts/evaluate_v2.py
"""

import sys
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_yolo_dataset_v2 import to_ir  # noqa: E402
from day5_evaluate import load_gt, match, prf  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "yolo_dataset_v2"
V1_DATA = ROOT / "data" / "yolo_dataset"
OUT = ROOT / "data" / "results" / "v2_evaluation.md"
MODELS = {
    "v1 (Week 1, YOLO11n)": ROOT / "runs" / "species_v1" / "weights" / "best.pt",
    "v2 (YOLO11n)": ROOT / "runs" / "species_v2" / "weights" / "best.pt",
    "v2 (YOLO12n)": ROOT / "runs" / "species_v12" / "weights" / "best.pt",
}
THRESHOLDS = [0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60]
FLOOR = 0.05
IMGSZ = 320
SCENES = {"prosopis_juliflora", "acacia_nilotica", "calotropis_procera", "saccharum_spontaneum",
          "tamarix_aphylla", "ziziphus_nummularia"}


def neg_group(stem):
    folder = next((f.name for f in (ROOT / "data" / "negatives").iterdir()
                   if f.is_dir() and stem.startswith(f"neg_{f.name}")), "other")
    return "people / everyday (COCO128)" if folder == "coco128" else \
        "empty habitat scenes" if folder in SCENES else "confuser animals"


def predict(model, files, ir=False):
    out = {}
    rng = np.random.default_rng(7)
    for f in files:
        src = to_ir(cv2.imread(str(f)), rng) if ir else str(f)
        r = model.predict(src, conf=FLOOR, imgsz=IMGSZ, verbose=False)[0]
        out[f.stem] = [(int(b.cls[0]), float(b.conf[0]), tuple(b.xyxyn[0].tolist())) for b in r.boxes]
    return out


def totals(preds, gts, t):
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    for s in preds:
        a, b, c = match(preds[s], gts[s], t)
        for d, e in ((tp, a), (fp, b), (fn, c)):
            for k, v in e.items():
                d[k] += v
    return tp, fp, fn


def main():
    seen_by_v1 = {f.stem for s in ("train", "val") for f in (V1_DATA / "images" / s).glob("*.jpg")}
    val = sorted((DATA / "images" / "val").glob("*.jpg"))
    test = [f for f in sorted((DATA / "images" / "test").glob("*.jpg")) if f.stem not in seen_by_v1]
    pos = [f for f in test if not f.stem.startswith("neg_")]
    neg = [f for f in test if f.stem.startswith("neg_")]
    gt_val = {f.stem: load_gt(DATA / "labels" / "val" / f"{f.stem}.txt") for f in val}
    gt_test = {f.stem: load_gt(DATA / "labels" / "test" / f"{f.stem}.txt") for f in pos}
    left_out = sum(1 for f in (DATA / "images" / "test").glob("*.jpg") if f.stem in seen_by_v1)

    # Ultralytics mAP needs a yaml; point it at a list of the filtered test images
    lst = DATA / "test_eval.txt"
    lst.write_text("\n".join(str(f) for f in test))
    names_yaml = (DATA / "data.yaml").read_text().split("names:")[1]
    yaml = DATA / "test_eval.yaml"
    yaml.write_text(f"path: {DATA.as_posix()}\ntrain: images/train\nval: {lst.as_posix()}\nnames:{names_yaml}")

    lines = ["## Species models on the v2 held-out test split\n",
             f"Test split: {len(pos)} animal photos ({sum(len(g) for g in gt_test.values())} boxes) and "
             f"{len(neg)} negative images. {left_out} test images that v1 had already seen were left out. "
             "Threshold for each model chosen on the v2 validation split.\n"]
    summary = ["| Model | conf (from val) | mAP@50 | mAP@50-95 | precision | recall | F1 | exact-species hit | "
               "false alarm on negatives | recall on synthetic IR |", "|---|---|---|---|---|---|---|---|---|---|"]
    per_sp, per_neg = {}, {}
    names = None

    for label, path in MODELS.items():
        if not path.exists():
            print(f"skip {label}: {path} missing")
            continue
        model = YOLO(str(path))
        names = model.names
        pv = predict(model, val)
        best_t, best_f1 = 0.25, -1
        for t in THRESHOLDS:
            tp, fp, fn = totals({s: pv[s] for s in gt_val}, gt_val, t)
            f1 = prf(sum(tp.values()), sum(fp.values()), sum(fn.values()))[2]
            if f1 > best_f1:
                best_t, best_f1 = t, f1

        m = model.val(data=str(yaml), split="val", imgsz=IMGSZ, verbose=False, plots=False)
        pt, ir = predict(model, pos), predict(model, pos, ir=True)
        pn = predict(model, neg)
        tp, fp, fn = totals(pt, gt_test, best_t)
        p, r, f1 = prf(sum(tp.values()), sum(fp.values()), sum(fn.values()))
        tpi, fpi, fni = totals(ir, gt_test, best_t)
        r_ir = prf(sum(tpi.values()), sum(fpi.values()), sum(fni.values()))[1]
        hit = sum(any(c == gt_test[s][0][0] and conf >= best_t for c, conf, _ in pt[s]) for s in pt) / len(pt)
        fa = [s for s in pn if any(conf >= best_t for _, conf, _ in pn[s])]
        summary.append(f"| {label} | {best_t:.2f} | {m.box.map50:.3f} | {m.box.map:.3f} | {p:.2f} | {r:.2f} | "
                       f"{f1:.2f} | {100 * hit:.0f}% | {100 * len(fa) / len(pn):.0f}% ({len(fa)}/{len(pn)}) | "
                       f"{r_ir:.2f} |")
        per_sp[label] = {k: prf(tp[k], fp[k], fn[k]) + (prf(tpi[k], fpi[k], fni[k])[1],) for k in names}
        groups = Counter(neg_group(s) for s in pn)
        hits = Counter(neg_group(s) for s in fa)
        per_neg[label] = {g: (hits[g], n) for g, n in groups.items()}
        print(summary[-1], flush=True)

    lines += summary
    lines += ["\nexact-species hit = share of test photos where the right species is named at the chosen conf. "
              "false alarm = share of negative images (no target species) that get any species box. "
              "Synthetic IR = the same test photos made grayscale, dark and noisy.\n",
              "### Per species (test split): precision / recall / recall on synthetic IR\n",
              "| Species | " + " | ".join(per_sp) + " |", "|---|" + "---|" * len(per_sp)]
    for k, sp in names.items():
        lines.append(f"| {sp} | " + " | ".join(f"{v[k][0]:.2f} / {v[k][1]:.2f} / {v[k][3]:.2f}"
                                                for v in per_sp.values()) + " |")
    lines += ["\n### False alarms by negative type (images with any species box / images)\n",
              "| Negative type | " + " | ".join(per_neg) + " |", "|---|" + "---|" * len(per_neg)]
    for g in sorted({g for v in per_neg.values() for g in v}):
        lines.append(f"| {g} | " + " | ".join(f"{v[g][0]} / {v[g][1]}" for v in per_neg.values()) + " |")

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
