"""
Day 2 - dataset availability survey.
For every candidate species, count research-grade, openly licensed iNaturalist
photos (a) inside Pakistan and (b) worldwide, and write a report.

Usage:
    python scripts/inat_survey.py
"""

import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from species_config import CANDIDATES, PLACE_ID_PAKISTAN

API = "https://api.inaturalist.org/v1"
LICENSES = "cc0,cc-by,cc-by-nc"  # licences allowed for academic use
OUT = Path(__file__).resolve().parent.parent / "data" / "dataset_survey.json"


def get(path, **params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def main():
    rows = []
    for key, (sci, common, oiv7) in CANDIDATES.items():
        # Exact name match: the search's first hit can be another species
        # ("Hyaena hyaena" used to return Crocuta crocuta, the spotted hyena).
        taxa = [t for t in get("taxa", q=sci, rank="species", per_page=10)["results"]
                if t["name"].lower() == sci.lower()]
        if not taxa:
            print(f"{sci}: taxon not found")
            continue
        taxon_id = taxa[0]["id"]
        common_args = dict(
            taxon_id=taxon_id,
            quality_grade="research",
            photo_license=LICENSES,
            per_page=0,
        )
        pk = get("observations", place_id=PLACE_ID_PAKISTAN, **common_args)["total_results"]
        world = get("observations", **common_args)["total_results"]
        rows.append(
            {"key": key, "scientific": sci, "common": common, "taxon_id": taxon_id,
             "oiv7_class": oiv7, "pakistan": pk, "worldwide": world}
        )
        print(f"{common:18s} taxon={taxon_id:<8} pakistan={pk:<6} worldwide={world}")
        time.sleep(1)  # be polite to the API

    OUT.write_text(json.dumps(rows, indent=2))
    print(f"\nSaved {OUT}")


if __name__ == "__main__":
    main()
