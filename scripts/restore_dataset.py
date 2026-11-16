"""
Restore the exact Day 2 dataset from data/dataset/attribution.csv.

download_dataset.py asks iNaturalist for a *random* sample, so re-running it
gives different photos. Every later result (Day 3 detections, Day 3 review,
the Day 5 pseudo-labels) is keyed to the original file names, so this script
re-downloads the same photos by their observation ids instead.

It also restores the v2 additions listed in data/dataset/manifest_v2.csv
(extra species photos, confuser animals and empty scenes from download_more.py),
which store the photo url directly.

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


def dest_of(r):
    """The Day 2 'striped_hyena' photos are all Crocuta crocuta (spotted hyena): the
    survey picked the wrong taxon. They are kept as spotted-hyena negatives."""
    if r["species"] == "striped_hyena":
        return ROOT.parent / "negatives" / "crocuta_crocuta" / r["file"].replace("striped_hyena", "crocuta_crocuta")
    return ROOT / r["species"] / r["file"]


def main():
    with open(ROOT / "attribution.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    missing = [r for r in rows if not dest_of(r).exists()]
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
        dest = dest_of(r)
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
    restore_v2()


def restore_v2():
    manifest = ROOT / "manifest_v2.csv"
    if not manifest.exists():
        return
    with open(manifest, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    base = {"species": ROOT, "confuser": ROOT.parent / "negatives", "scene": ROOT.parent / "negatives"}
    todo = [(base[r["group"]] / r["file"].rsplit("_", 1)[0] / r["file"], r["url"]) for r in rows]
    todo = [(d, u) for d, u in todo if not d.exists()]
    print(f"v2 manifest: {len(rows)} photos listed, {len(todo)} to download")
    failed = 0
    for n, (dest, url) in enumerate(todo, 1):
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = get(url, binary=True)
        if data:
            dest.write_bytes(data)
        else:
            failed += 1
        if n % 100 == 0:
            print(f"  {n}/{len(todo)}")
    print(f"v2 done, {failed} failed")


if __name__ == "__main__":
    main()
