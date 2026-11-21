"""
Day 6 - video detection pipeline (visual branch of the base paper).

Base paper (Velpula et al. 2026) architecture:
  input layer       camera / video file          (here: OpenCV)
  processing layer  YOLO visual detection        (here)  + YAMNet audio (later week)
  fusion layer      confirm with both modalities (later week, once audio exists)
  output layer      on-screen boxes, alerts, CSV detection log   (here)

Three detectors run on each processed frame:
  - the fine-tuned species model (8 target species, from scripts/train.py)
  - a COCO model restricted to 'person', for the human-intrusion / poaching alert,
    since the species model has no human class
  - a small open-vocabulary model (YOLO-World, prompt "animal") that finds animals
    the species model does not know; these are reported as 'unknown_animal'
    instead of being forced into one of the 8 species (turn off with --no-unknown)

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
SPECIES_MODEL = ROOT / "runs" / "species_v2" / "weights" / "best.pt"
PERSON_MODEL = "yolo11n.pt"  # COCO, class 0 = person
COOLDOWN_SEC = 10
BANNER_SEC = 3  # an alert stays on screen this long in the annotated video
SPECIES_COLOR = (0, 200, 0)
PERSON_COLOR = (0, 0, 255)
UNKNOWN_COLOR = (0, 165, 255)
GENERIC_MODEL = ROOT / "models" / "yolov8s-worldv2.pt"
GENERIC_PROMPTS = ["animal", "bird", "reptile"]
UNKNOWN_CONF = 0.35   # open-vocab boxes are noisier, so a higher bar
PERSON_CONF = 0.40    # the COCO person model fired on crocodiles and nilgai at 0.25-0.4
OUT_WIDTH = 960  # annotated video is downscaled to keep files small
# When a species box and a person box cover the same object, the more confident one wins.
# (v1 always trusted a person box above 0.5, which turned crocodiles and nilgai into people;
# the v2 species model was trained with people as negatives, so it rarely fires on hikers.)
OVERLAP = 0.6       # intersection / smaller box area


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
                if p[1] > s[1]:
                    drop_s.add(i)
                else:
                    drop_p.add(j)
    return ([s for i, s in enumerate(species) if i not in drop_s]
            + [p for j, p in enumerate(persons) if j not in drop_p])


def load_generic():
    m = YOLO(str(GENERIC_MODEL))
    m.set_classes(GENERIC_PROMPTS)
    return m


def detect(species_model, person_model, frame, conf, species_imgsz, generic_model=None):
    """Return [(label, conf, (x1, y1, x2, y2), is_person), ...] for one frame."""
    species, persons = [], []
    r = species_model.predict(frame, conf=conf, imgsz=species_imgsz, verbose=False)[0]
    for b in r.boxes:
        species.append((species_model.names[int(b.cls[0])], float(b.conf[0]),
                        tuple(int(v) for v in b.xyxy[0].tolist()), False))
    r = person_model.predict(frame, conf=max(conf, PERSON_CONF), classes=[0], verbose=False)[0]
    for b in r.boxes:
        persons.append(("person", float(b.conf[0]), tuple(int(v) for v in b.xyxy[0].tolist()), True))
    found = resolve(species, persons)
    if generic_model is not None:
        r = generic_model.predict(frame, conf=max(conf, UNKNOWN_CONF), verbose=False)[0]
        for b in r.boxes:
            box = tuple(int(v) for v in b.xyxy[0].tolist())
            if all(overlap(box, f[2]) < 0.3 for f in found):
                found.append(("unknown_animal", float(b.conf[0]), box, False))
    return found


def draw(frame, found):
    for label, c, (x1, y1, x2, y2), is_person in found:
        color = PERSON_COLOR if is_person else UNKNOWN_COLOR if label == "unknown_animal" else SPECIES_COLOR
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = f"{label} {c:.2f}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 8)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(frame, text, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def draw_alerts(frame, recent, t):
    """Banner at the top of the frame for alerts raised in the last BANNER_SEC seconds."""
    y = 8
    for t0, kind, label, c in recent:
        if t - t0 > BANNER_SEC:
            continue
        text = f"ALERT  {kind}: {label} ({c:.2f})  at {t0:.1f}s"
        color = (0, 0, 200) if kind == "HUMAN INTRUSION" else (0, 140, 0)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(frame, (8, y), (8 + tw + 16, y + th + 16), color, -1)
        cv2.putText(frame, text, (16, y + th + 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        y += th + 22


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="video file, or a webcam index such as 0")
    parser.add_argument("--species-model", default=str(SPECIES_MODEL))
    parser.add_argument("--species-imgsz", type=int, default=320, help="size the species model was trained at")
    parser.add_argument("--conf", type=float, default=0.3)
    parser.add_argument("--every", type=int, default=3, help="run detection every N frames, reuse boxes between")
    parser.add_argument("--show", action="store_true", help="show a live window (press q to stop)")
    parser.add_argument("--no-unknown", action="store_true", help="skip the unknown-animal detector")
    parser.add_argument("--out", default=str(OUT), help="output folder")
    args = parser.parse_args()
    out = Path(args.out)

    species_model = YOLO(args.species_model)
    person_model = YOLO(PERSON_MODEL)
    generic_model = None if args.no_unknown else load_generic()

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

    out.mkdir(parents=True, exist_ok=True)
    stem = f"webcam{args.source}" if is_cam else Path(args.source).stem
    writer = cv2.VideoWriter(str(out / f"{stem}_annotated.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), fps, out_size)
    det_file = open(out / f"{stem}_detections.csv", "w", newline="", encoding="utf-8")
    alert_file = open(out / f"{stem}_alerts.csv", "w", newline="", encoding="utf-8")
    det_log, alert_log = csv.writer(det_file), csv.writer(alert_file)
    det_log.writerow(["timestamp", "video_time_s", "frame", "label", "conf", "x1", "y1", "x2", "y2"])
    alert_log.writerow(["timestamp", "video_time_s", "label", "conf", "type"])

    last_alert, recent, found, idx, n_det = {}, [], [], 0, 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        t = idx / fps
        if idx % args.every == 0:
            found = detect(species_model, person_model, frame, args.conf, args.species_imgsz, generic_model)
            now = datetime.now().isoformat(timespec="seconds")
            for label, c, box, is_person in found:
                det_log.writerow([now, f"{t:.2f}", idx, label, f"{c:.3f}", *box])
                n_det += 1
                if t - last_alert.get(label, -COOLDOWN_SEC) >= COOLDOWN_SEC:
                    last_alert[label] = t
                    kind = "HUMAN INTRUSION" if is_person else "WILDLIFE"
                    alert_log.writerow([now, f"{t:.2f}", label, f"{c:.3f}", kind])
                    recent = [a for a in recent if t - a[0] <= BANNER_SEC] + [(t, kind, label, c)]
                    print(f"[ALERT {t:6.1f}s] {kind}: {label} ({c:.2f})")
        draw(frame, found)
        frame = cv2.resize(frame, out_size) if scale < 1 else frame
        draw_alerts(frame, recent, t)
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
    print(f"\n{idx} frames, {n_det} detections logged. Outputs in {out}")


if __name__ == "__main__":
    main()
