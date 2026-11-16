"""
Week 1 fixes - grow the dataset.

1. Tops every target species up to --per-species photos (iNaturalist research
   grade, open licence, not captive). Photos already on disk are kept.
2. Downloads "confuser" animals that the model mixes up with our species
   (chital, blackbuck, dog, cattle, ...). They are used as negative images:
   the model must learn NOT to call them nilgai / chinkara / jackal.
3. Downloads empty habitat scenes (landscape photos of grassland / scrub
   habitats, no animal) as negatives.

Every photo is recorded in data/dataset/manifest_v2.csv (observation id + photo
url) so the exact set can be restored with scripts/restore_dataset.py --manifest.

Usage:
    python scripts/download_more.py --per-species 300 --per-confuser 80
"""

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "data"
API = "https://api.inaturalist.org/v1"
LICENSES = "cc0,cc-by,cc-by-nc"
UA = {"User-Agent": "fyp-wildlife-dataset/1.0"}

TARGETS = {
    "leopard": 41963, "chinkara": 42253, "wild_boar": 42134, "striped_hyena": 41888,  # Hyaena hyaena (41886 is Crocuta crocuta, the spotted hyena)
    "golden_jackal": 851014, "indian_peafowl": 1204, "nilgai": 42426, "mugger": 26063,
}

# Animals seen in our test clips / habitat that the Week 1 model confused with targets
CONFUSERS = [
    "Axis axis",             # chital - called nilgai in peafowl_running
    "Antilope cervicapra",   # blackbuck - looks like chinkara / nilgai
    "Aepyceros melampus",    # impala - the gazelle_hluhluwe clip
    "Canis familiaris",      # dog - looks like jackal
    "Bos taurus",            # cattle - looks like nilgai
    "Bubalus bubalis",       # water buffalo - looks like wild boar / nilgai
    "Vulpes bengalensis",    # Bengal fox - looks like jackal
    "Crocuta crocuta",       # spotted hyena - not a target (kept out of striped_hyena)
    "Felis chaus",           # jungle cat - looks like leopard at distance
    "Herpestes edwardsii",   # Indian grey mongoose
    "Varanus bengalensis",   # monitor lizard - looks like mugger
    "Ardea cinerea",         # grey heron - big bird near water (person false alarms)
    "Ciconiidae",            # storks - false person on bird
    "Capra hircus",          # goat
]

# Empty-scene negatives: photos of habitat plants usually show open ground
SCENE_TAXA = ["Prosopis juliflora", "Acacia nilotica", "Calotropis procera", "Saccharum spontaneum",
              "Tamarix aphylla", "Ziziphus nummularia"]


def get_json(url):
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r)
        except Exception as e:
            wait = 5 * (attempt + 1)
            print(f"  api error ({e}), retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"failed: {url}")


def taxon_id(name):
    res = get_json(f"{API}/taxa?" + urllib.parse.urlencode({"q": name, "per_page": 5}))["results"]
    for t in res:
        if t["name"].lower() == name.lower():
            return t["id"]
    return res[0]["id"]


def observations(tid, want, skip_ids, captive="false", quality="research"):
    """Yield up to `want` new observations, oldest-id-first paging (deterministic)."""
    got, id_above = 0, 0
    while got < want:
        q = {"taxon_id": tid, "quality_grade": quality, "photo_license": LICENSES,
             "photos": "true", "per_page": 200, "order_by": "id", "order": "asc", "id_above": id_above}
        if captive is not None:
            q["captive"] = captive
        res = get_json(f"{API}/observations?" + urllib.parse.urlencode(q))["results"]
        time.sleep(1.0)
        if not res:
            return
        for o in res:
            id_above = o["id"]
            if o["id"] in skip_ids or not o.get("photos"):
                continue
            yield o
            got += 1
            if got >= want:
                return


def download(o, dest):
    photo = o["photos"][0]
    url = photo["url"].replace("square", "large")
    if not dest.exists():
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=40) as r:
                    dest.write_bytes(r.read())
                break
            except Exception as e:
                print(f"  photo {o['id']} error ({e})")
                time.sleep(3)
        else:
            return None
    return [o["id"], url, photo.get("license_code"), photo.get("attribution"), o.get("uri")]


def existing_ids(folder):
    return {int(p.stem.rsplit("_", 1)[1]) for p in folder.glob("*.jpg") if p.stem.rsplit("_", 1)[1].isdigit()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-species", type=int, default=300)
    ap.add_argument("--per-confuser", type=int, default=80)
    ap.add_argument("--per-scene", type=int, default=40)
    args = ap.parse_args()

    manifest = ROOT / "dataset" / "manifest_v2.csv"
    rows = []
    if manifest.exists():
        with open(manifest, encoding="utf-8") as f:
            rows = list(csv.reader(f))[1:]
    known = {(r[0], r[1]) for r in rows}

    jobs = [("species", k, tid, args.per_species, "false") for k, tid in TARGETS.items()]
    jobs += [("confuser", n.lower().replace(" ", "_"), None, args.per_confuser, None) for n in CONFUSERS]
    jobs += [("scene", n.lower().replace(" ", "_"), None, args.per_scene, None) for n in SCENE_TAXA]

    for group, key, tid, want, captive in jobs:
        folder = ROOT / ("dataset" if group == "species" else "negatives") / key
        folder.mkdir(parents=True, exist_ok=True)
        have = existing_ids(folder)
        need = want - len(have)
        if need <= 0:
            print(f"{group:8s} {key:22s} already {len(have)}")
            continue
        tid = tid or taxon_id(key.replace("_", " "))
        # Dogs, cattle, goats, buffalo are almost always "captive"/domestic on iNat
        cap = captive if group == "species" else None
        quality = "research" if group != "scene" else "research,needs_id"
        obs = list(observations(tid, need, have, captive=cap, quality=quality))
        with ThreadPoolExecutor(max_workers=6) as pool:
            recs = list(pool.map(lambda o: download(o, folder / f"{key}_{o['id']}.jpg"), obs))
        n = 0
        for o, rec in zip(obs, recs):
            name = f"{key}_{o['id']}.jpg"
            if rec and (group, name) not in known:
                rows.append([group, name, *rec])
                known.add((group, name))
                n += 1
        print(f"{group:8s} {key:22s} +{n} (now {len(have) + n})", flush=True)
        with open(manifest, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["group", "file", "observation_id", "url", "license", "attribution", "source_url"])
            w.writerows(rows)

    print(f"Done. Manifest: {manifest}")


if __name__ == "__main__":
    main()
