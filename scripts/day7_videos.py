"""
Day 7 - test the complete prototype on the 14 Day 3 video clips.

Frames are sampled every 0.5 s (same as Day 3). On every sampled frame both
systems run:
  pretrained  yolov8m-oiv7 (Day 3 setup); correct = the species' own OIV7 class
  prototype   fine-tuned species model + COCO person model (video_pipeline.py);
              correct = the species label
and per clip we count frames with the correct label, frames with a wrong
species label, and frames with a false person.

Usage:
    python scripts/day7_videos.py
"""

import sys
from collections import Counter
from pathlib import Path

import cv2
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_pretrained import ANIMALS, EXPECTED, HUMAN, MODEL as PRETRAINED  # noqa: E402
from video_pipeline import PERSON_MODEL, SPECIES_MODEL, detect  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "data"
OUT = ROOT / "results" / "day7_video_summary.md"
SAMPLE_EVERY_SEC = 0.5
CONF = 0.25  # overwritten by --conf
# clip -> expected label (None = no target species in the clip)
EXPECT = {
    "leopard_india": "leopard", "leopard_tree": "leopard",
    "boar_berlin": "wild_boar", "boar_bulgaria": "wild_boar",
    "jackals": "golden_jackal", "peafowl_walking": "indian_peafowl",
    "peafowl_running": "indian_peafowl", "nilgai_zoo": "nilgai",
    "hyena_spotted": "striped_hyena", "crocodile_nile": "mugger", "gazelle_hluhluwe": "chinkara",
    "camtrap_general": None, "camtrap_jaguarundi": None, "human_hiking": "person",
}


def main():
    conf = float(sys.argv[sys.argv.index("--conf") + 1]) if "--conf" in sys.argv else CONF
    pre = YOLO(PRETRAINED)
    species, person = YOLO(str(SPECIES_MODEL)), YOLO(PERSON_MODEL)
    lines = [f"## Pretrained vs prototype on the test clips (conf >= {conf}, frame every {SAMPLE_EVERY_SEC}s)\n",
             "Each cell: frames with the correct label / frames with a wrong species label / frames with a false person.\n",
             "| Clip | expected | frames | pretrained OIV7 | prototype | prototype labels (count) |",
             "|---|---|---|---|---|---|"]
    for f in sorted((ROOT / "sample_videos").glob("*.webm")):
        exp = EXPECT[f.stem]
        exact = HUMAN if exp == "person" else (EXPECTED[exp][0] if exp else set())
        cap = cv2.VideoCapture(str(f))
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not 1 <= fps <= 120:  # broken metadata (seen on boar_berlin)
            fps = 30
        step = max(1, round(fps * SAMPLE_EVERY_SEC))
        idx, n = 0, 0
        a, b = Counter(), Counter()  # pretrained / prototype: ok, wrong, person
        labels = Counter()
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0 and frame.mean() > 3:  # skip fully black frames
                n += 1
                r = pre.predict(frame, conf=conf, agnostic_nms=True, verbose=False)[0]
                got = {pre.names[int(x.cls[0])] for x in r.boxes} & (ANIMALS | HUMAN)
                a["ok"] += bool(got & exact)
                a["wrong"] += bool((got & ANIMALS) - exact - {"Animal", "Mammal"})
                a["person"] += exp != "person" and bool(got & HUMAN)

                found = detect(species, person, frame, conf, 320)
                got = {lab for lab, *_ in found}
                labels.update(lab for lab, *_ in found)
                b["ok"] += exp in got
                b["wrong"] += bool(got - {exp, "person"})
                b["person"] += exp != "person" and "person" in got
            idx += 1
        cap.release()
        cell = lambda c: f"{c['ok']} / {c['wrong']} / {c['person']}"
        top = ", ".join(f"{k} ({v})" for k, v in labels.most_common(3)) or "-"
        lines.append(f"| {f.stem} | {exp or 'none'} | {n} | {cell(a)} | {cell(b)} | {top} |")
        print(lines[-1])

    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
