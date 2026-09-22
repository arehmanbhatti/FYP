"""
Day 3 - corrected detection rates after manual review.

The 116 images in which the model found no animal (conf >= 0.25) were checked
by eye (contact sheets in data/results/day3/review_*.jpg) and labelled:
  E - no live animal in the photo (tracks, scat, skull, carcass, landscape ...)
      -> a bad dataset image, not a model failure
  S - animal present but tiny / hidden / camouflaged / mostly in water
  A - animal clearly visible, the model simply missed it (true miss)

Usage:
    python scripts/day3_adjusted.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_pretrained import EXPECTED, outcome  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent / "data" / "results"
REPORT_T = 0.25

# labels for data/results/day3/review_items.json, in the same order
LABELS = ("EEESESSEESASSEEA" "EEEEEEE" "EEAEESEEAESEEEESE" "SESEESESEESSEAE"
          "AEAAAASAE" "EESSSEAEEAAAESS" "ESEEAS" "SSESESA" "SSSASSEASASEESEESSEASAES")


def main():
    items = json.loads((ROOT / "day3" / "review_items.json").read_text())
    dets = json.loads((ROOT / "day3_detections.json").read_text())
    assert len(items) == len(LABELS), (len(items), len(LABELS))
    label = dict(zip(items, LABELS))

    lines = [f"## Corrected results after manual review (conf >= {REPORT_T})\n",
             "| Species | images | bad images (E) | valid | exact hit | exact+family hit | "
             "small/hidden miss (S) | clear-animal miss (A) |",
             "|---|---|---|---|---|---|---|---|"]
    for sp in EXPECTED:
        keys = [k for k in dets if k.startswith(sp + "/")]
        lab = Counter(label[k] for k in keys if k in label)
        valid = len(keys) - lab["E"]
        oc = Counter(outcome(sp, dets[k], REPORT_T) for k in keys)
        pct = lambda n: f"{n} ({100 * n / valid:.0f}%)"
        lines.append(f"| {sp} | {len(keys)} | {lab['E']} | {valid} | {pct(oc['exact'])} | "
                     f"{pct(oc['exact'] + oc['family'])} | {lab['S']} | {lab['A']} |")

    text = "\n".join(lines)
    (ROOT / "day3_adjusted.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
