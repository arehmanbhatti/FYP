"""
Week 1 fixes - build the v2 training set.

What changed against build_yolo_dataset.py (v1):
  * More photos: up to 300 per species (scripts/download_more.py).
  * Better pseudo-labels: boxes from TWO detectors are merged (class-agnostic NMS)
      - Open Images V7 YOLOv8m, kept when its class fits the species family (v1 rule)
      - YOLO-World v2 (open vocabulary), prompted with the species name and "animal"
    One detector often catches what the other misses (World is weak on crocodiles,
    OIV7 on hyena / jackal). Images where neither finds an animal are dropped
    (tracks, scat, skulls, empty photos).
  * Negative images with an empty label file (the model must predict nothing):
      - confuser animals (chital, blackbuck, impala, dog, cattle, ...)
      - empty habitat scenes
      - people and everyday scenes (COCO128)
  * Synthetic night / IR copies of 30% of the training images (grayscale, dark,
    noisy, blurred) since no real IR camera-trap photos are available yet.
  * Three splits: train 70% / val 15% / test 15%. The split comes from a hash of the
    file name, so adding photos later never moves an old photo to another split.
    The test split is never used during training or threshold tuning.

Boxes are still automatic. data/results/v2_review/ gets contact sheets so they can be
checked by eye (or the dataset can be uploaded to Roboflow for review).

Usage:
    python scripts/build_yolo_dataset_v2.py            # uses cached labels if present
    python scripts/build_yolo_dataset_v2.py --relabel  # rerun both detectors
"""

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import torch
from torchvision.ops import nms

sys.path.insert(0, str(Path(__file__).resolve().parent))
from day3_adjusted import LABELS  # noqa: E402
from evaluate_pretrained import ANIMALS, EXPECTED, GENERIC  # noqa: E402

PROJECT = Path(__file__).resolve().parent.parent
ROOT = PROJECT / "data"
OUT = ROOT / "yolo_dataset_v2"
CACHE = ROOT / "results" / "autolabels_v2.json"
CLASSES = list(EXPECTED)
IR_SHARE = 0.30
OIV7_CONF, WORLD_CONF, NMS_IOU = 0.25, 0.20, 0.5
MIN_AREA = 0.002  # drop specks smaller than 0.2% of the image

WORLD_PROMPT = {
    "leopard": "leopard", "chinkara": "gazelle", "wild_boar": "wild boar",
    "striped_hyena": "hyena", "golden_jackal": "jackal", "indian_peafowl": "peacock",
    "nilgai": "antelope", "mugger": "crocodile",
}
COCO128 = "https://github.com/ultralytics/assets/releases/download/v0.0.0/coco128.zip"


def split_of(name):
    h = int(hashlib.md5(name.encode()).hexdigest(), 16) % 100
    return "train" if h < 70 else "val" if h < 85 else "test"


def no_animal_set():
    review = json.loads((ROOT / "results" / "day3" / "review_items.json").read_text())
    return {k for k, lab in zip(review, LABELS) if lab == "E"}


def autolabel(files_by_species):
    from ultralytics import YOLO
    oiv7 = YOLO(str(PROJECT / "yolov8m-oiv7.pt"))
    world = YOLO(str(PROJECT / "models" / "yolov8x-worldv2.pt"))
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    for sp, files in files_by_species.items():
        family = EXPECTED[sp][1]
        world.set_classes([WORLD_PROMPT[sp], "animal", "person"])
        todo = [f for f in files if f"{sp}/{f.name}" not in cache]
        print(f"labelling {sp}: {len(todo)} new", flush=True)
        for f in todo:
            boxes = []
            r = oiv7.predict(str(f), conf=OIV7_CONF, agnostic_nms=True, verbose=False, device=0)[0]
            for b in r.boxes:
                name = r.names[int(b.cls)]
                if name in ANIMALS and name in family | GENERIC:
                    boxes.append(([round(v, 1) for v in b.xyxy[0].tolist()], round(float(b.conf), 3), "oiv7"))
            r = world.predict(str(f), conf=WORLD_CONF, imgsz=640, verbose=False, device=0)[0]
            for b in r.boxes:
                if int(b.cls) < 2:  # species prompt or "animal", not person
                    boxes.append(([round(v, 1) for v in b.xyxy[0].tolist()], round(float(b.conf), 3), "world"))
            cache[f"{sp}/{f.name}"] = {"wh": list(r.orig_shape[::-1]), "boxes": boxes}
        CACHE.write_text(json.dumps(cache))
    return cache


def merge(entry):
    if not entry["boxes"]:
        return []
    w, h = entry["wh"]
    xyxy = torch.tensor([b[0] for b in entry["boxes"]], dtype=torch.float32)
    conf = torch.tensor([b[1] for b in entry["boxes"]], dtype=torch.float32)
    keep = nms(xyxy, conf, NMS_IOU).tolist()
    out = []
    for i in keep:
        x1, y1, x2, y2 = xyxy[i].tolist()
        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)
        if (x2 - x1) * (y2 - y1) / (w * h) >= MIN_AREA:
            out.append((x1, y1, x2, y2))
    return out


def to_ir(img, rng):
    """Approximate a night IR camera-trap frame."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    g = np.power(g, rng.uniform(1.2, 1.8)) * rng.uniform(0.45, 0.8)  # darker, IR-flash falloff
    h, w = g.shape
    yy, xx = np.mgrid[0:h, 0:w]
    vignette = 1 - 0.55 * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / 2
    g = g * vignette + rng.normal(0, rng.uniform(0.02, 0.06), g.shape)
    g = cv2.GaussianBlur(np.clip(g, 0, 1), (0, 0), rng.uniform(0.6, 1.4))
    return cv2.cvtColor((g * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)


def coco128_negatives():
    dest = ROOT / "negatives" / "coco128"
    if dest.exists() and any(dest.iterdir()):
        return
    dest.mkdir(parents=True, exist_ok=True)
    tmp = ROOT / "negatives" / "coco128.zip"
    urllib.request.urlretrieve(COCO128, tmp)
    with zipfile.ZipFile(tmp) as z:
        for n in z.namelist():
            if n.endswith(".jpg"):
                (dest / Path(n).name).write_bytes(z.read(n))
    tmp.unlink()


def write_review_sheets(samples):
    """Contact sheets of merged boxes, 30 images each, for checking by eye."""
    out = ROOT / "results" / "v2_review"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    by_sp = {}
    for path, sp, boxes in samples:
        by_sp.setdefault(sp, []).append((path, boxes))
    for sp, items in by_sp.items():
        for s in range(0, len(items), 30):
            tiles = []
            for path, boxes in items[s:s + 30]:
                img = cv2.imread(str(path))
                for x1, y1, x2, y2 in boxes:
                    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), max(2, img.shape[1] // 200))
                tile = cv2.resize(img, (256, 192))
                cv2.putText(tile, path.stem[-12:], (4, 186), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
                tiles.append(tile)
            while len(tiles) % 6:
                tiles.append(np.zeros_like(tiles[0]))
            rows = [np.hstack(tiles[i:i + 6]) for i in range(0, len(tiles), 6)]
            cv2.imwrite(str(out / f"{sp}_{s // 30:02d}.jpg"), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--relabel", action="store_true")
    args = ap.parse_args()
    if args.relabel and CACHE.exists():
        CACHE.unlink()

    bad = no_animal_set()
    files = {sp: sorted(f for f in (ROOT / "dataset" / sp).glob("*.jpg") if f"{sp}/{f.name}" not in bad)
             for sp in CLASSES}
    cache = autolabel(files)
    coco128_negatives()

    if OUT.exists():
        shutil.rmtree(OUT)
    for s in ("train", "val", "test"):
        (OUT / "images" / s).mkdir(parents=True)
        (OUT / "labels" / s).mkdir(parents=True)

    rng = np.random.default_rng(42)
    stats = {sp: Counter() for sp in CLASSES}
    review = []
    for cid, sp in enumerate(CLASSES):
        for f in files[sp]:
            boxes = merge(cache[f"{sp}/{f.name}"])
            if not boxes:
                stats[sp]["dropped"] += 1
                continue
            w, h = cache[f"{sp}/{f.name}"]["wh"]
            lines = "\n".join(f"{cid} {(x1 + x2) / 2 / w:.6f} {(y1 + y2) / 2 / h:.6f} "
                              f"{(x2 - x1) / w:.6f} {(y2 - y1) / h:.6f}" for x1, y1, x2, y2 in boxes) + "\n"
            s = split_of(f.name)
            shutil.copy(f, OUT / "images" / s / f.name)
            (OUT / "labels" / s / (f.stem + ".txt")).write_text(lines)
            stats[sp][s] += 1
            review.append((f, sp, boxes))
            if s == "train" and rng.random() < IR_SHARE:
                ir_name = f.stem + "_ir.jpg"
                cv2.imwrite(str(OUT / "images" / s / ir_name), to_ir(cv2.imread(str(f)), rng))
                (OUT / "labels" / s / (f.stem + "_ir.txt")).write_text(lines)
                stats[sp]["ir"] += 1

    neg = Counter()
    for folder in sorted((ROOT / "negatives").iterdir()):
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.jpg")):
            s = split_of(f.name)
            name = f"neg_{folder.name}_{f.name}" if not f.name.startswith(folder.name) else f"neg_{f.name}"
            shutil.copy(f, OUT / "images" / s / name)
            (OUT / "labels" / s / (Path(name).stem + ".txt")).write_text("")
            neg[s] += 1
            if s == "train" and rng.random() < IR_SHARE / 2:
                cv2.imwrite(str(OUT / "images" / s / (Path(name).stem + "_ir.jpg")), to_ir(cv2.imread(str(f)), rng))
                (OUT / "labels" / s / (Path(name).stem + "_ir.txt")).write_text("")
                neg["ir"] += 1

    names = "\n".join(f"  {i}: {sp}" for i, sp in enumerate(CLASSES))
    (OUT / "data.yaml").write_text(f"path: {OUT.as_posix()}\ntrain: images/train\nval: images/val\n"
                                   f"test: images/test\nnames:\n{names}\n")
    write_review_sheets(review)

    lines = ["| Species | photos | dropped (no box) | train | +IR copies | val | test |", "|---|---|---|---|---|---|---|"]
    for sp, c in stats.items():
        lines.append(f"| {sp} | {len(files[sp])} | {c['dropped']} | {c['train']} | {c['ir']} | {c['val']} | {c['test']} |")
    lines.append(f"| negatives | {sum(neg[s] for s in ('train', 'val', 'test'))} | - | {neg['train']} | {neg['ir']} | {neg['val']} | {neg['test']} |")
    table = "\n".join(lines)
    (ROOT / "results" / "v2_dataset_summary.md").write_text("## v2 training set\n\n" + table + "\n")
    print(table)
    print(f"\nWritten to {OUT}")


if __name__ == "__main__":
    main()
