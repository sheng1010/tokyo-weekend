import json
import os
import sys
import time
import subprocess

from sources.mori import fetch_mori_exhibitions
from sources.tobikan import fetch_tobikan_exhibitions
from sources.mot import fetch_mot_exhibitions
from sources.tnm import fetch_tnm_exhibitions
from sources.nact import fetch_nact_exhibitions
from merger.exhibition_merger import merge_exhibitions


RAW_OUTPUT_PATH = "data/raw_events.json"
MAIN_LOCK_FILE = "main.lock"
BUILD_LOCK_FILE = "build_events.lock"


def normalize_raw_event(item):
    return {
        "id": item.get("id"),
        "slug": item.get("slug", ""),
        "title": item.get("title", ""),
        "category": item.get("category", "Exhibition"),
        "location": item.get("location", ""),
        "venue": item.get("venue", ""),
        "date": item.get("date", ""),
        "startDate": item.get("startDate", ""),
        "endDate": item.get("endDate", ""),
        "image": item.get("image", ""),
        "access": item.get("access", ""),
        "price": item.get("price", ""),
        "bookingUrl": item.get("bookingUrl", ""),
        "source": item.get("source", ""),
        "sourceUrl": item.get("sourceUrl", ""),
        "tags": item.get("tags", []),
        "area": item.get("area", ""),
        "language": item.get("language", "en"),
        "rawDescription": item.get("rawDescription", []),
    }


def dedupe_raw_events(events):
    seen = {}

    for item in events:
        key = item.get("sourceUrl") or item.get("slug") or str(item.get("id"))
        if key not in seen:
            seen[key] = item

    return list(seen.values())


def ensure_single_main_instance():
    if os.path.exists(MAIN_LOCK_FILE):
        print("=== main.py skipped (already running) ===")
        sys.exit(0)

    with open(MAIN_LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(f"pid={os.getpid()} started_at={time.time()}\n")


def cleanup_main_lock():
    if os.path.exists(MAIN_LOCK_FILE):
        os.remove(MAIN_LOCK_FILE)


def run_build_events():
    raw_file = "data/raw_events.json"
    output_file = "data/generated_events.json"

    if os.path.exists(BUILD_LOCK_FILE):
        print("=== build_events.py skipped (already running) ===")
        return

    if os.path.exists(raw_file) and os.path.exists(output_file):
        raw_mtime = os.path.getmtime(raw_file)
        output_mtime = os.path.getmtime(output_file)

        if output_mtime >= raw_mtime:
            print("=== build_events.py skipped (generated file already up to date) ===")
            return

    try:
        with open(BUILD_LOCK_FILE, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()} started_at={time.time()}\n")

        print("=== running build_events.py ===")
        subprocess.run([sys.executable, "build_events.py"], check=True)
        print("=== build_events.py finished ===")
    finally:
        if os.path.exists(BUILD_LOCK_FILE):
            os.remove(BUILD_LOCK_FILE)


def main():
    ensure_single_main_instance()

    try:
        print(f"=== start script pid={os.getpid()} at {time.time()} ===")

        all_events = []

        mori_exhibitions = []
        tobikan_exhibitions = []
        mot_exhibitions = []
        tnm_exhibitions = []
        nact_exhibitions = []

        try:
            print("before mori exhibitions")
            mori_exhibitions = fetch_mori_exhibitions()
            print("after mori exhibitions:", len(mori_exhibitions))
        except Exception as e:
            print("[MORI] failed:", e)

        try:
            print("before tobikan exhibitions")
            tobikan_exhibitions = fetch_tobikan_exhibitions()
            print("after tobikan exhibitions:", len(tobikan_exhibitions))
        except Exception as e:
            print("[TOBIKAN] failed:", e)

        try:
            print("before mot exhibitions")
            mot_exhibitions = fetch_mot_exhibitions()
            print("after mot exhibitions:", len(mot_exhibitions))
        except Exception as e:
            print("[MOT] failed:", e)

        try:
            print("before tnm exhibitions")
            tnm_exhibitions = fetch_tnm_exhibitions()
            print("after tnm exhibitions:", len(tnm_exhibitions))
        except Exception as e:
            print("[TNM] failed:", e)

        try:
            print("before nact exhibitions")
            nact_exhibitions = fetch_nact_exhibitions()
            print("after nact exhibitions:", len(nact_exhibitions))
        except Exception as e:
            print("[NACT] failed:", e)

        merged_exhibitions = merge_exhibitions(
            mori_exhibitions,
            tobikan_exhibitions,
            mot_exhibitions,
            tnm_exhibitions,
            nact_exhibitions,
        )

        print("merged exhibitions:", len(merged_exhibitions))

        all_events.extend(merged_exhibitions)
        all_events = [normalize_raw_event(item) for item in all_events]
        all_events = dedupe_raw_events(all_events)

        print("before write raw file")
        with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(all_events, f, ensure_ascii=False, indent=2)
        print("after write raw file")

        print("raw_events.json updated:", len(all_events))

        run_build_events()

        print("=== end script ===")

    finally:
        cleanup_main_lock()


if __name__ == "__main__":
    main()