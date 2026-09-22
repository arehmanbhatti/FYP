"""
Day 3 - evaluate the pretrained OIV7 model on the Day 2 dataset.

Runs the model once at a low confidence floor (0.10) and stores every
detection, so the accuracy-vs-threshold trade-off (Day 5) can be computed
without re-running inference.

Per image the outcome at a threshold is one of:
  exact    - a detection of the species' own OIV7 class (e.g. Leopard for leopard)
  family   - no exact class, but a plausible related class (e.g. Cat, Antelope)
  generic  - only the vague classes Animal / Mammal
  wrong    - detections exist but none of them are plausible for the species
  none     - nothing detected

Usage:
    python scripts/evaluate_pretrained.py
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent / "data"
MODEL = "yolov8m-oiv7.pt"
FLOOR = 0.10
THRESHOLDS = [0.10, 0.25, 0.30, 0.50, 0.70]
REPORT_T = 0.25

GENERIC = {"Animal", "Mammal"}
# OIV7 animal classes. Tree / Plant / Flower etc. are background objects: they are
# reported as false detections but never count as the animal being found or misclassified.
ANIMALS = {
    "Alpaca", "Animal", "Antelope", "Armadillo", "Bat (Animal)", "Bear", "Bird", "Blue jay",
    "Brown bear", "Bull", "Camel", "Canary", "Carnivore", "Cat", "Cattle", "Cheetah", "Chicken",
    "Crocodile", "Deer", "Dinosaur", "Dog", "Dolphin", "Duck", "Eagle", "Elephant", "Falcon",
    "Fox", "Frog", "Giraffe", "Goat", "Goose", "Hamster", "Harbor seal", "Hedgehog", "Hippopotamus",
    "Horse", "Jaguar (Animal)", "Kangaroo", "Koala", "Leopard", "Lion", "Lizard", "Lynx", "Magpie",
    "Mammal", "Marine mammal", "Monkey", "Mouse", "Mule", "Ostrich", "Otter", "Owl", "Panda",
    "Parrot", "Penguin", "Pig", "Polar bear", "Porcupine", "Rabbit", "Raccoon", "Raven",
    "Red panda", "Reptile", "Rhinoceros", "Sea lion", "Sheep", "Skunk", "Snake", "Sparrow",
    "Squirrel", "Swan", "Tiger", "Tortoise", "Turkey", "Turtle", "Whale", "Woodpecker", "Zebra",
}
HUMAN = {"Person", "Man", "Woman", "Boy", "Girl", "Human face", "Human head", "Human body"}
# species -> (exact classes, plausible related classes)
EXPECTED = {
    "leopard":        ({"Leopard"},   {"Leopard", "Jaguar (Animal)", "Cheetah", "Cat", "Tiger", "Lion"}),
    "chinkara":       ({"Antelope"},  {"Antelope", "Deer", "Goat", "Sheep"}),
    "wild_boar":      ({"Pig"},       {"Pig"}),
    "striped_hyena":  (set(),         {"Dog", "Fox", "Carnivore"}),
    "golden_jackal":  ({"Dog"},       {"Dog", "Fox", "Carnivore"}),
    "indian_peafowl": ({"Bird"},      {"Bird"}),
    "nilgai":         ({"Antelope"},  {"Antelope", "Deer", "Cattle", "Bull", "Horse", "Goat"}),
    "mugger":         ({"Crocodile"}, {"Crocodile", "Reptile", "Lizard"}),
}


def outcome(species, dets, t):
    exact, family = EXPECTED[species]
    kept = [d for d in dets if d["conf"] >= t and d["cls"] in ANIMALS]
    if not kept:
        return "none"
    names = {d["cls"] for d in kept}
    if names & exact:
        return "exact"
    if names & family:
        return "family"
    if names & GENERIC:
        return "generic"
    return "wrong"


def main():
    det_file = ROOT / "results" / "day3_detections.json"
    if det_file.exists() and "--rerun" not in sys.argv:
        all_dets = json.loads(det_file.read_text())  # reuse cached inference
    else:
        model = YOLO(MODEL)
        all_dets = {}
        for sp in EXPECTED:
            files = sorted((ROOT / "dataset" / sp).glob("*.jpg"))
            for r in model.predict(source=[str(f) for f in files], conf=FLOOR,
                                   agnostic_nms=True, stream=True, verbose=False):
                all_dets[f"{sp}/{Path(r.path).name}"] = [
                    {"cls": model.names[int(b.cls[0])], "conf": round(float(b.conf[0]), 3),
                     "box": [round(v) for v in b.xyxy[0].tolist()]}
                    for b in r.boxes
                ]
            print(f"done {sp} ({len(files)} images)")
        det_file.write_text(json.dumps(all_dets))

    # ---- summaries ----
    by_sp = defaultdict(list)
    for key, dets in all_dets.items():
        by_sp[key.split("/")[0]].append((key, dets))

    lines = [f"## Outcome per species at conf >= {REPORT_T}\n",
             "| Species | n | exact | family | generic | wrong | none | mean conf (exact) |",
             "|---|---|---|---|---|---|---|---|"]
    fp_by_sp = {}
    for sp, items in by_sp.items():
        c = Counter(outcome(sp, d, REPORT_T) for _, d in items)
        confs = [max(x["conf"] for x in d if x["cls"] in EXPECTED[sp][0])
                 for _, d in items
                 if any(x["cls"] in EXPECTED[sp][0] and x["conf"] >= REPORT_T for x in d)]
        mean = f"{sum(confs) / len(confs):.2f}" if confs else "-"
        n = len(items)
        lines.append(f"| {sp} | {n} | {c['exact']} | {c['family']} | {c['generic']} | "
                     f"{c['wrong']} | {c['none']} | {mean} |")
        # false detections at >= T, split by kind (counted per detection, not per image)
        kept = [x for _, d in items for x in d if x["conf"] >= REPORT_T]
        fp_by_sp[sp] = {
            "background": Counter(x["cls"] for x in kept if x["cls"] not in ANIMALS | HUMAN),
            "human": Counter(x["cls"] for x in kept if x["cls"] in HUMAN),
            "wrong_animal": Counter(x["cls"] for x in kept if x["cls"] in ANIMALS
                                    and x["cls"] not in EXPECTED[sp][1] | GENERIC),
        }

    lines += ["\n## Exact-class hit rate vs threshold (% of images)\n",
              "| Species | " + " | ".join(f"{t}" for t in THRESHOLDS) + " |",
              "|---|" + "---|" * len(THRESHOLDS)]
    for sp, items in by_sp.items():
        row = [f"{100 * sum(outcome(sp, d, t) == 'exact' for _, d in items) / len(items):.0f}%"
               for t in THRESHOLDS]
        lines.append(f"| {sp} | " + " | ".join(row) + " |")

    lines += ["\n## Any plausible (exact + family) rate vs threshold (% of images)\n",
              "| Species | " + " | ".join(f"{t}" for t in THRESHOLDS) + " |",
              "|---|" + "---|" * len(THRESHOLDS)]
    for sp, items in by_sp.items():
        row = [f"{100 * sum(outcome(sp, d, t) in ('exact', 'family') for _, d in items) / len(items):.0f}%"
               for t in THRESHOLDS]
        lines.append(f"| {sp} | " + " | ".join(row) + " |")

    lines += [f"\n## False detections at conf >= {REPORT_T} (per detection)\n",
              "| Species | wrong animal class | human | background objects |", "|---|---|---|---|"]
    fmt = lambda c: ", ".join(f"{k} ({v})" for k, v in c.most_common(5)) or "-"
    for sp, fp in fp_by_sp.items():
        lines.append(f"| {sp} | {fmt(fp['wrong_animal'])} | {fmt(fp['human'])} | {fmt(fp['background'])} |")

    text = "\n".join(lines)
    (ROOT / "results" / "day3_summary.md").write_text(text, encoding="utf-8")
    print("\n" + text)


if __name__ == "__main__":
    main()
