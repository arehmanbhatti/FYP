"""
Day 3 (video gap) - download a small curated set of openly licensed test videos
from Wikimedia Commons into data/sample_videos/ and write attribution.csv.

Role:
  target   - the real target species
  standin  - close relative used only because no free footage of the target
             species exists (NOT the target species)
  camtrap  - trail-camera style footage (night / IR / low quality)
  human    - people, for the human-detection class

Usage:
    python scripts/download_videos.py
"""

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "sample_videos"
UA = "FYP-wildlife-research/1.0 (student final-year project)"

# local name -> (Commons title, role, what it is)
VIDEOS = {
    "leopard_india":     ("Leopard (Panthera pardus), in Uttarakhand, India.webm", "target", "leopard"),
    "leopard_tree":      ("Leopard (Panthera pardus) female resting in a tree ....webm", "target", "leopard"),
    "boar_bulgaria":     ("Sus scrofa-wild boars-Bulgaria VP8.webm", "target", "wild boar"),
    "boar_berlin":       ("Wild boars in a park in Berlin-Spandau 02.webm", "target", "wild boar"),
    "jackals":           ("Jackals.webm", "target", "jackal (species to be confirmed)"),
    "peafowl_running":   ("Running Indian peafowl (Pavo cristatus).webm", "target", "Indian peafowl"),
    "peafowl_walking":   ("Peacock walking and eating.webm", "target", "Indian peafowl"),
    "nilgai_zoo":        ("Zoo de La Fleche 20180601 6.webm", "target", "nilgai (zoo)"),
    "hyena_spotted":     ("Spotted Hyena (Crocuta crocuta).webm", "standin", "spotted hyena for striped hyena"),
    "crocodile_nile":    ("Nairobi National Park (August 2025) Nile crocodile.webm", "standin", "Nile crocodile for mugger"),
    "gazelle_hluhluwe":  ("Gazelle in Hluhluwe.webm", "standin", "gazelle for chinkara"),
    "camtrap_general":   ("Trail Camera.webm", "camtrap", "trail camera footage"),
    "camtrap_jaguarundi": ("Jaguarundi-santa-fe-do-sul-brazil-camera-trap.webm", "camtrap", "jaguarundi camera trap"),
    "human_hiking":      ("Working through COVID-19 (20200716-FS-MtBaker-responsiblehiking-001).webm", "human", "hikers"),
}


def api(**params):
    params["format"] = "json"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(12):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(3 + attempt)
    raise RuntimeError("Commons API unreachable")


def download(url, dest):
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"    retry {attempt + 1}: {e}")
            time.sleep(4 + attempt * 2)
    dest.unlink(missing_ok=True)
    return False


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, (title, role, what) in VIDEOS.items():
        pages = api(action="query", titles="File:" + title, prop="imageinfo",
                    iiprop="url|size|extmetadata")["query"]["pages"]
        info = next(iter(pages.values())).get("imageinfo")
        if not info:
            print(f"{name}: NOT FOUND on Commons ({title})")
            continue
        info = info[0]
        meta = info.get("extmetadata", {})
        ext = Path(urllib.parse.urlparse(info["url"]).path).suffix
        dest = OUT / f"{name}{ext}"
        if dest.exists():
            print(f"{name}: already downloaded")
        else:
            print(f"{name}: downloading {info['size'] / 1e6:.1f} MB")
            if not download(info["url"], dest):
                print(f"  FAILED {name}")
                continue
        rows.append([dest.name, role, what,
                     meta.get("LicenseShortName", {}).get("value", ""),
                     re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip(),
                     info["descriptionurl"]])
        time.sleep(1)

    with open(OUT / "attribution.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["file", "role", "content", "license", "author", "source_url"])
        w.writerows(rows)
    print(f"Done: {len(rows)}/{len(VIDEOS)} videos, attribution in {OUT / 'attribution.csv'}")


if __name__ == "__main__":
    main()
