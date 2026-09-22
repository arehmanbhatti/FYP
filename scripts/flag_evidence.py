"""
Day 3 - flag dataset images that show evidence of an animal (tracks, scat,
bones, feathers ...) instead of the animal itself, using iNaturalist's
"Evidence of Presence" annotation. Un-annotated images stay 'unknown'.

Writes data/dataset/evidence_flags.json: {"<species>/<file>": "organism" | "evidence" | "unknown"}

Usage:
    python scripts/flag_evidence.py
"""

import csv
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data" / "dataset"
API = "https://api.inaturalist.org/v1"


def get(path, tries=5):
    for i in range(tries):
        try:
            with urllib.request.urlopen(f"{API}/{path}", timeout=30) as r:
                return json.load(r)
        except Exception as e:
            print(f"  retry {i + 1}: {e}")
            time.sleep(5)
    raise RuntimeError(f"API failed: {path}")


def main():
    terms = get("controlled_terms")["results"]
    term = next(t for t in terms if t["label"] == "Evidence of Presence")
    organism_id = next(v["id"] for v in term["values"] if v["label"] == "Organism")
    print(f"term {term['id']} '{term['label']}', organism value id {organism_id}")

    rows = list(csv.DictReader(open(ROOT / "attribution.csv", encoding="utf-8")))
    flags = {}
    for i in range(0, len(rows), 50):
        chunk = rows[i:i + 50]
        ids = ",".join(r["observation_id"] for r in chunk)
        by_id = {str(o["id"]): o for o in get(f"observations?id={ids}&per_page=50")["results"]}
        for r in chunk:
            ann = [a for a in by_id[r["observation_id"]].get("annotations", [])
                   if a["controlled_attribute_id"] == term["id"]]
            if not ann:
                state = "unknown"
            else:  # majority of votes decides; ties -> evidence
                good = sum(a["controlled_value_id"] == organism_id for a in ann)
                state = "organism" if good > len(ann) - good else "evidence"
            flags[f"{r['species']}/{r['file']}"] = state
        time.sleep(1)

    (ROOT / "evidence_flags.json").write_text(json.dumps(flags, indent=1))
    from collections import Counter
    for sp in sorted({k.split("/")[0] for k in flags}):
        c = Counter(v for k, v in flags.items() if k.startswith(sp + "/"))
        print(f"{sp:15s} {dict(c)}")


if __name__ == "__main__":
    main()
