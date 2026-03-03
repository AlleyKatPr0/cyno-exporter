import argparse
import os
import time
import urllib.parse
from pathlib import Path
from urllib import request
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, Counter

CDN_BASE = "https://resources.eveonline.com/"

# -----------------------------
# INDEX PARSING
# -----------------------------

def parse_index(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.lstrip("\ufeff").strip()
            if not line or line.startswith("#"):
                continue

            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue

            virtual_path = parts[0]
            cdn_key = parts[1]

            yield {
                "virtual": virtual_path,
                "cdn": cdn_key,
                "prefix": cdn_key[:2]
            }

# -----------------------------
# URL + PATH
# -----------------------------

def make_url(cdn_key):
    return CDN_BASE + urllib.parse.quote(cdn_key, safe="/")

def target_path(out_dir, cdn_key):
    return Path(out_dir) / cdn_key

# -----------------------------
# DOWNLOAD
# -----------------------------

def download_one(entry, out_dir, retries=3):
    cdn_key = entry["cdn"]
    url = make_url(cdn_key)
    dest = target_path(out_dir, cdn_key)

    if dest.exists():
        return (cdn_key, True, "exists")

    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp = dest.with_suffix(".part")

    headers = {
        "User-Agent": "EVECdnDownloader/2.0",
        "Referer": "https://www.eveonline.com/"
    }

    for attempt in range(retries):
        try:
            req = request.Request(url, headers=headers)
            with request.urlopen(req, timeout=30) as resp:
                with open(tmp, "wb") as wf:
                    wf.write(resp.read())

            os.replace(tmp, dest)
            return (cdn_key, True, None)

        except Exception as e:
            time.sleep(2 ** attempt)

    return (cdn_key, False, str(e))

# -----------------------------
# PREFIX GROUPING
# -----------------------------

def group_by_prefix(entries):
    grouped = defaultdict(list)
    for e in entries:
        grouped[e["prefix"]].append(e)
    return grouped

# -----------------------------
# MAIN
# -----------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--index", required=True)
    p.add_argument("--out", default="eve_assets")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--stats", action="store_true",
                   help="Show prefix distribution only")
    args = p.parse_args()

    entries = list(parse_index(args.index))

    print(f"Loaded {len(entries)} entries.")

    grouped = group_by_prefix(entries)

    # PREFIX ANALYSIS MODE
    if args.stats:
        print("\nPrefix distribution:")
        counts = Counter(e["prefix"] for e in entries)
        for pfx, cnt in counts.most_common():
            print(f"{pfx}: {cnt}")
        return

    # DOWNLOAD MODE
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading using prefix grouping ({len(grouped)} buckets)...")

    futures = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for prefix, group in grouped.items():
            for entry in group:
                futures.append(pool.submit(download_one, entry, out_dir))

        ok = 0
        fail = 0

        for fut in as_completed(futures):
            key, success, msg = fut.result()
            if success:
                ok += 1
            else:
                fail += 1
                print("FAIL:", key, msg)

    print(f"Done. OK={ok} FAIL={fail}")

if __name__ == "__main__":
    main()