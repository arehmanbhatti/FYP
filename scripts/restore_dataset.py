"""
Restore the exact Day 2 dataset from data/dataset/attribution.csv.

download_dataset.py asks iNaturalist for a *random* sample, so re-running it
gives different photos. Every later result (Day 3 detections, Day 3 review,
the Day 5 pseudo-labels) is keyed to the original file names, so this script
re-downloads the same photos by their observation ids instead.

Usage:
    python scripts/restore_dataset.py
"""

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.inaturalist.org/v1/observations"
ROOT = Path(__file__).resolve().parent.parent / "data" / "dataset"
UA = "FYP-wildlife-research/1.0 (student final-year project)"
BATCH = 100


def get(url, binary=False):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read() if binary else json.load(r)
        except Exception as e:
            print(f"    retry {attempt + 1}: {e}")
            time.sleep(3 + attempt * 2)
    return None


def main():
    with open(ROOT / "attribution.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    missing = [r for r in rows if not (ROOT / r["species"] / r["file"]).exists()]
    print(f"{len(rows)} photos listed, {len(missing)} to download")

    urls = {}
    ids = [r["observation_id"] for r in missing]
    for i in range(0, len(ids), BATCH):
        chunk = ids[i:i + BATCH]
        q = urllib.parse.urlencode({"id": ",".join(chunk), "per_page": BATCH})
        data = get(f"{API}?{q}")
        for o in (data or {}).get("results", []):
            if o.get("photos"):
                # same choice as download_dataset.py: first photo, 'large' size
                urls[str(o["id"])] = o["photos"][0]["url"].replace("square", "large")
        time.sleep(1)

    failed = []
    for n, r in enumerate(missing, 1):
        dest = ROOT / r["species"] / r["file"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = urls.get(r["observation_id"])
        data = get(url, binary=True) if url else None
        if not data:
            failed.append(r["file"])
            continue
        dest.write_bytes(data)
        if n % 50 == 0:
            print(f"  {n}/{len(missing)}")
        time.sleep(0.3)

    print(f"Done. {len(missing) - len(failed)} downloaded, {len(failed)} failed")
    for f in failed:
        print("  FAILED", f)


if __name__ == "__main__":
    main()
