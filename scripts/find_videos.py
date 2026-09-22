"""
Day 3 (video gap) - find openly licensed wildlife videos on Wikimedia Commons.
Searches per target species, keeps only freely reusable licences, and writes
the candidate list (with url, size, duration, licence, author) to
data/video_candidates.json for review before anything is downloaded.

Usage:
    python scripts/find_videos.py
"""

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "video_candidates.json"
UA = "FYP-wildlife-research/1.0 (student final-year project)"
FREE = re.compile(r"^(cc0|cc-by|cc-by-sa|pd|public domain)", re.I)

QUERIES = {
    "leopard": ["leopard", "Panthera pardus"],
    "chinkara": ["chinkara", "Gazella bennettii", "Indian gazelle"],
    "wild_boar": ["wild boar", "Sus scrofa"],
    "striped_hyena": ["striped hyena", "Hyaena hyaena"],
    "golden_jackal": ["golden jackal", "Canis aureus"],
    "indian_peafowl": ["Indian peafowl", "peacock Pavo cristatus"],
    "nilgai": ["nilgai", "Boselaphus tragocamelus"],
    "mugger": ["mugger crocodile", "Crocodylus palustris"],
    "human": ["camera trap human", "people walking forest"],
}


def api(**params):
    params["format"] = "json"
    url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for attempt in range(12):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(3 + attempt)
    raise RuntimeError("Commons API unreachable")


def main():
    found = {}
    for species, terms in QUERIES.items():
        for term in terms:
            data = api(action="query", generator="search", gsrnamespace=6, gsrlimit=15,
                       gsrsearch=f"{term} filetype:video", prop="imageinfo",
                       iiprop="url|size|mime|extmetadata|mediatype")
            for page in data.get("query", {}).get("pages", {}).values():
                info = page["imageinfo"][0]
                meta = info.get("extmetadata", {})
                lic = meta.get("LicenseShortName", {}).get("value", "")
                if not FREE.match(lic.replace(" ", "-").replace("Public-domain", "pd")) \
                        and "public domain" not in lic.lower() and not lic.lower().startswith("cc"):
                    continue
                found[page["title"]] = {
                    "species": species, "title": page["title"], "url": info["url"],
                    "size_mb": round(info["size"] / 1e6, 1), "mime": info["mime"],
                    "width": info.get("width"), "height": info.get("height"),
                    "license": lic,
                    "author": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")),
                    "page": info["descriptionurl"],
                }
            time.sleep(1.5)
        n = sum(1 for v in found.values() if v["species"] == species)
        print(f"{species:15s} {n} free videos")

    OUT.write_text(json.dumps(list(found.values()), indent=1))
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
