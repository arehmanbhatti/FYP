"""
Day 6 - video detection pipeline (visual branch of the base paper).

Base paper (Velpula et al. 2026) architecture:
  input layer       camera / video file          (here: OpenCV)
  processing layer  YOLO visual detection        (here)  + YAMNet audio (later week)
  fusion layer      confirm with both modalities (later week, once audio exists)
  output layer      on-screen boxes, alerts, CSV detection log   (here)

Two detectors run on each processed frame:
  - the fine-tuned species model (8 target species, from scripts/train.py)
  - a COCO model restricted to 'person', for the human-intrusion / poaching alert,
    since the species model has no human class

Outputs in data/results/pipeline/:
  <video>_annotated.mp4   frames with boxes and labels
  <video>_detections.csv  every detection: time, frame, label, confidence, box
  <video>_alerts.csv      one alert per label per COOLDOWN_SEC of video

Usage:
    python scripts/video_pipeline.py --source data/sample_videos/leopard_india.webm
    python scripts/video_pipeline.py --source 0 --show      (webcam)
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "results" / "pipeline"
SPECIES_MODEL = ROOT / "runs" / "species_v1" / "weights" / "best.pt"
PERSON_MODEL = "yolo11n.pt"  # COCO, class 0 = person
COOLDOWN_SEC = 10
SPECIES_COLOR = (0, 200, 0)
PERSON_COLOR = (0, 0, 255)
OUT_WIDTH = 960  # annotated video is downscaled to keep files small
# The species model never saw people in training, so it labels hikers as nilgai/peafowl
# with high confidence. When a species box and a person box cover the same object, the
# COCO person model wins if it is confident; otherwise the person box is the false one.
OVERLAP = 0.6       # intersection / smaller box area
PERSON_TRUST = 0.5


def overlap(a, b):
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    smaller = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return ix * iy / smaller if smaller > 0 else 0.0


def resolve(species, persons):
    """Drop the losing box wherever a species box and a person box cover the same object."""
    drop_s, drop_p = set(), set()
    for i, s in enumerate(species):
        for j, p in enumerate(persons):
            if overlap(s[2], p[2]) >= OVERLAP:
                (drop_s if p[1] >= PERSON_TRUST else drop_p).add(i if p[1] >= PERSON_TRUST else j)
    return ([s for i, s in enumerate(species) if i not in drop_s]
            + [p for j, p in enumerate(persons) if j not in drop_p])


def detect(species_model, person_model, frame, conf, species_imgsz):
    """Return [(label, conf, (x1, y1, x2, y2), is_person), ...] for one frame."""
    species, persons = [], []
    r = species_model.predict(frame, conf=conf, imgsz=species_imgsz, verbose=False)[0]
    for b in r.boxes:
        species.append((species_model.names[int(b.cls[0])], float(b.conf[0]),
                        tuple(int(v) for v in b.xyxy[0].tolist()), False))
    r = person_model.predict(frame, conf=conf, classes=[0], verbose=False)[0]
    for b in r.boxes:
        persons.append(("person", float(b.conf[0]), tuple(int(v) for v in b.xyxy[0].tolist()), True))
    return resolve(species, persons)


def draw(frame, found):
    for label, c, (x1, y1, x2, y2), is_person in found:
        color = PERSON_COLOR if is_person else SPECIES_COLOR
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f"{label} {c:.2f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 8)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="video file, or a webcam index such as 0")
    parser.add_argument("--species-model", default=str(SPECIES_MODEL))
    parser.add_argument("--species-imgsz", type=int, default=320, help="size the species model was trained at")
    parser.add_argument("--conf", type=float, default=0.3)
    parser.add_argument("--every", type=int, default=3, help="run detection every N frames, reuse boxes between")
    parser.add_argument("--show", action="store_true", help="show a live window (press q to stop)")
    args = parser.parse_args()

    species_model = YOLO(args.species_model)
    person_model = YOLO(PERSON_MODEL)

    is_cam = args.source.isdigit()
    cap = cv2.VideoCapture(int(args.source) if is_cam else args.source)
    if not cap.isOpened():
        raise SystemExit(f"Cannot open {args.source}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    if not 1 <= fps <= 120:  # broken metadata (seen on boar_berlin)
        fps = 30
    w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    scale = min(1.0, OUT_WIDTH / w)
    out_size = (round(w * scale), round(h * scale))

    OUT.mkdir(parents=True, exist_ok=True)
    stem = f"webcam{args.source}" if is_cam else Path(args.source).stem
    writer = cv2.VideoWriter(str(OUT / f"{stem}_annotated.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, out_size)
    det_file = open(OUT / f"{stem}_detections.csv", "w", newline="", encoding="utf-8")
    alert_file = open(OUT / f"{stem}_alerts.csv", "w", newline="", encoding="utf-8")
    det_log, alert_log = csv.writer(det_file), csv.writer(alert_file)
    det_log.writerow(["timestamp", "video_time_s", "frame", "label", "conf", "x1", "y1", "x2", "y2"])
    alert_log.writerow(["timestamp", "video_time_s", "label", "conf", "type"])

    last_alert, found, idx, n_det = {}, [], 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = idx / fps
        if idx % args.every == 0:
            found = detect(species_model, person_model, frame, args.conf, args.species_imgsz)
            now = datetime.now().isoformat(timespec="seconds")
            for label, c, box, is_person in found:
                det_log.writerow([now, f"{t:.2f}", idx, label, f"{c:.3f}", *box])
                n_det += 1
                if t - last_alert.get(label, -COOLDOWN_SEC) >= COOLDOWN_SEC:
                    last_alert[label] = t
                    kind = "HUMAN INTRUSION" if is_person else "WILDLIFE"
                    alert_log.writerow([now, f"{t:.2f}", label, f"{c:.3f}", kind])
                    print(f"[ALERT {t:6.1f}s] {kind}: {label} ({c:.2f})")
        draw(frame, found)
        frame = cv2.resize(frame, out_size) if scale < 1 else frame
        writer.write(frame)
        if args.show:
            cv2.imshow("wildlife monitor", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        idx += 1

    cap.release()
    writer.release()
    det_file.close()
    alert_file.close()
    cv2.destroyAllWindows()
    print(f"\n{idx} frames, {n_det} detections logged. Outputs in {OUT}")


if __name__ == "__main__":
    main()
