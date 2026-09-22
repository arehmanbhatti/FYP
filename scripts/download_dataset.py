"""
Day 2 - build the initial dataset from iNaturalist.
Downloads research-grade, openly licensed, non-captive photos for the final
target species into data/dataset/<species>/ and writes an attribution CSV.

Usage:
    python scripts/download_dataset.py --per-species 60
"""

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from species_config import CANDIDATES

API = "https://api.inaturalist.org/v1/observations"
LICENSES = "cc0,cc-by,cc-by-nc"
ROOT = Path(__file__).resolve().parent.parent / "data"

# Final Week 1 target species (see README, Day 2)
TARGETS = [
    "leopard", "chinkara", "wild_boar", "striped_hyena",
    "golden_jackal", "indian_peafowl", "nilgai", "mugger",
]


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-species", type=int, default=60)
    args = parser.parse_args()

    survey = {r["key"]: r for r in json.loads((ROOT / "dataset_survey.json").read_text())}
    rows = []

    for key in TARGETS:
        taxon_id = survey[key]["taxon_id"]
        out_dir = ROOT / "dataset" / key
        out_dir.mkdir(parents=True, exist_ok=True)

        query = urllib.parse.urlencode({
            "taxon_id": taxon_id, "quality_grade": "research",
            "photo_license": LICENSES, "captive": "false",
            "order_by": "random", "per_page": args.per_species,
            "photos": "true",
        })
        obs = fetch_json(f"{API}?{query}")["results"]

        saved = 0
        for o in obs:
            photo = o["photos"][0]
            url = photo["url"].replace("square", "large")
            dest = out_dir / f"{key}_{o['id']}.jpg"
            if not dest.exists():
                try:
                    urllib.request.urlretrieve(url, dest)
                except Exception as e:
                    print(f"  skip {o['id']}: {e}")
                    continue
                time.sleep(0.3)
            saved += 1
            rows.append([key, dest.name, o["id"], photo.get("license_code"),
                         photo.get("attribution"), o.get("uri")])
        print(f"{key:15s} downloaded {saved}/{len(obs)}")

    with open(ROOT / "dataset" / "attribution.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["species", "file", "observation_id", "license", "attribution", "source_url"])
        w.writerows(rows)
    print("Done. Attribution saved to data/dataset/attribution.csv")


if __name__ == "__main__":
    main()
