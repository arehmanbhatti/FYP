"""
Day 3 - run the pretrained model on the test videos.
Reads frames sequentially with OpenCV, samples about 2 frames per second, runs
YOLO, and reports per video: frames with any animal/human, class counts,
confidence, and the best frame (saved with boxes drawn).

Usage:
    python scripts/evaluate_videos.py
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_pretrained import ANIMALS, HUMAN, MODEL  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "data"
OUT = ROOT / "results" / "videos"
CONF = 0.25
SAMPLE_EVERY_SEC = 0.5


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    model = YOLO(MODEL)
    roles = {r["file"]: r for r in csv.DictReader(open(ROOT / "sample_videos" / "attribution.csv", encoding="utf-8"))}
    report = {}
    lines = ["| Video | role | frames tested | frames with animal/human | top classes (count) | best conf |",
             "|---|---|---|---|---|---|"]

    for f in sorted((ROOT / "sample_videos").glob("*.webm")):
        cap = cv2.VideoCapture(str(f))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not 1 <= fps <= 120:  # broken metadata (seen on boar_berlin)
            fps = 30
        step = max(1, round(fps * SAMPLE_EVERY_SEC))
        idx, tested, hit_frames = 0, 0, 0
        classes, best = Counter(), (0, None, None)
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0 and frame.mean() > 3:  # skip fully black frames
                tested += 1
                r = model.predict(frame, conf=CONF, agnostic_nms=True, verbose=False)[0]
                keep = [b for b in r.boxes if model.names[int(b.cls[0])] in ANIMALS | HUMAN]
                if keep:
                    hit_frames += 1
                    for b in keep:
                        classes[model.names[int(b.cls[0])]] += 1
                    top = max(float(b.conf[0]) for b in keep)
                    if top > best[0]:
                        best = (top, r.plot(), idx)
            idx += 1
        cap.release()
        if best[1] is not None:
            cv2.imwrite(str(OUT / f"{f.stem}_best.jpg"), cv2.resize(best[1], (960, 540)))
        role = roles.get(f.name, {}).get("role", "")
        top_cls = ", ".join(f"{k} ({v})" for k, v in classes.most_common(4)) or "-"
        report[f.stem] = {"role": role, "frames_read": idx, "tested": tested,
                          "hit_frames": hit_frames, "classes": dict(classes), "best_conf": round(best[0], 2)}
        lines.append(f"| {f.stem} | {role} | {tested} | {hit_frames} | {top_cls} | {best[0]:.2f} |")
        print(f"{f.stem:20s} tested={tested:3d} hits={hit_frames:3d} {top_cls}")

    (OUT / "video_report.json").write_text(json.dumps(report, indent=1))
    (OUT / "video_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
