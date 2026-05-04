import os
import time
import json
import re
from sources.mori import fetch_mori_exhibitions
from sources.sompo import fetch_sompo_exhibitions
from sources.artizon import fetch_artizon_exhibitions
from sources.momat import fetch_momat_exhibitions
from sources.nmwa import fetch_nmwa_exhibitions
from sources.designsight_2121 import fetch_2121_exhibitions
from sources.tobikan import fetch_tobikan_exhibitions
from sources.mot import fetch_mot_exhibitions
from sources.tnm import fetch_tnm_exhibitions
from sources.nact import fetch_nact_exhibitions
from sources.toho_films import fetch_toho_now_showing_films
from sources.tokyo109_films import fetch_109_now_showing_films
from sources.clubberia_nightlife import fetch_clubberia_nightlife
from sources.enter_nightlife import fetch_enter_nightlife
from sources.gotokyo_activities import fetch_gotokyo_activities
from utils.common_utils import repair_text_encoding

RAW_OUTPUT_PATH = "data/raw_events.json"
MAIN_LOCK_FILE = "main.lock"
BUILD_LOCK_FILE = "build_events.lock"

def normalize_raw_event(item):
    screening_venues = []
    for venue in item.get("screeningVenues", []):
        screening_venues.append({
            "name": repair_text_encoding(venue.get("name", "")),
            "address": repair_text_encoding(venue.get("address", "")),
        })

    return {
        "id": item.get("id"),
        "slug": repair_text_encoding(item.get("slug", "")),
        "title": repair_text_encoding(item.get("title", "")),
        "category": repair_text_encoding(item.get("category", "Exhibition")),
        "location": repair_text_encoding(item.get("location", "")),
        "venue": repair_text_encoding(item.get("venue", "")),
        "date": repair_text_encoding(item.get("date", "")),
        "startDate": repair_text_encoding(item.get("startDate", "")),
        "endDate": repair_text_encoding(item.get("endDate", "")),
        "image": repair_text_encoding(item.get("image", "")),
        "access": repair_text_encoding(item.get("access", "")),
        "price": repair_text_encoding(item.get("price", "")),
        "bookingUrl": repair_text_encoding(item.get("bookingUrl", "")),
        "source": repair_text_encoding(item.get("source", "")),
        "sourceUrl": repair_text_encoding(item.get("sourceUrl", "")),
        "tags": item.get("tags", []),
        "area": repair_text_encoding(item.get("area", "")),
        "language": repair_text_encoding(item.get("language", "en")),
        "director": repair_text_encoding(item.get("director", "")),
        "cast": repair_text_encoding(item.get("cast", "")),
        "screeningVenues": screening_venues,
        "rawDescription": item.get("rawDescription", []),
    }

def dedupe_raw_events(events):
    seen = {}
    for item in events:
        key = build_dedupe_key(item)
        if key not in seen:
            seen[key] = item
    return list(seen.values())

def normalize_key_text(value):
    text = repair_text_encoding(value or "").lower().strip()
    text = re.sub(r"[\s\-–—・:：!！?？\"'“”‘’「」『』（）()\[\]【】／/.,]+", "", text)
    return text

def build_dedupe_key(item):
    category = repair_text_encoding(item.get("category", "")).lower()
    if category == "film":
        return normalize_key_text(item.get("title")) + normalize_key_text(item.get("venue"))
    if category == "nightlife":
        return normalize_key_text(item.get("title")) + normalize_key_text(item.get("venue"))
    return item.get("sourceUrl") or item.get("slug") or str(item.get("id"))

def ensure_single_main_instance():
    if os.path.exists(MAIN_LOCK_FILE):
        print("Another instance is running. Exiting.")
        exit(1)
    with open(MAIN_LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def cleanup_main_lock():
    if os.path.exists(MAIN_LOCK_FILE):
        os.remove(MAIN_LOCK_FILE)

def run_build_events():
    import subprocess
    if os.path.exists(BUILD_LOCK_FILE):
        print("Build is already running. Skipping.")
        return
    with open(BUILD_LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    try:
        subprocess.run(["python", "build_events.py"], check=True)
    finally:
        if os.path.exists(BUILD_LOCK_FILE):
            os.remove(BUILD_LOCK_FILE)

def main():
    ensure_single_main_instance()
    try:
        print(f"=== start script pid={os.getpid()} at {time.time()} ===")
        all_events = []

        # 抓取所有来源
        all_events.extend(fetch_mori_exhibitions())
        all_events.extend(fetch_sompo_exhibitions())
        all_events.extend(fetch_artizon_exhibitions())
        all_events.extend(fetch_momat_exhibitions())
        all_events.extend(fetch_nmwa_exhibitions())
        all_events.extend(fetch_2121_exhibitions())
        all_events.extend(fetch_tobikan_exhibitions())
        all_events.extend(fetch_mot_exhibitions())
        all_events.extend(fetch_tnm_exhibitions())
        all_events.extend(fetch_nact_exhibitions())
        all_events.extend(fetch_toho_now_showing_films())
        all_events.extend(fetch_109_now_showing_films())
        all_events.extend(fetch_clubberia_nightlife())
        all_events.extend(fetch_enter_nightlife())
        all_events.extend(fetch_gotokyo_activities())

        # 规范化
        normalized_events = [normalize_raw_event(item) for item in all_events]

        # 去重
        deduped_events = dedupe_raw_events(normalized_events)

        # 写入
        with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(deduped_events, f, ensure_ascii=False, indent=2)

        print(f"抓取完成，共 {len(deduped_events)} 个事件。")

        # 构建
        run_build_events()

    finally:
        cleanup_main_lock()

if __name__ == "__main__":
    main()
