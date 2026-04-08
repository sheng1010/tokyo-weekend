import json
import os
import re
import sys
import time
import subprocess

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
from merger.exhibition_merger import merge_exhibitions
from utils.common_utils import repair_text_encoding


RAW_OUTPUT_PATH = "data/raw_events.json"
MAIN_LOCK_FILE = "main.lock"
BUILD_LOCK_FILE = "build_events.lock"

PLACEHOLDER_IMAGE_PATTERNS = (
    "no_image",
    "noimage",
    "sakuhin_nothing",
    "comingsoon_noimg",
)


def normalize_raw_event(item):
    screening_venues = []
    for venue in item.get("screeningVenues", []):
        screening_venues.append(
            {
                "name": repair_text_encoding(venue.get("name", "")),
                "code": repair_text_encoding(venue.get("code", "")),
                "url": repair_text_encoding(venue.get("url", "")),
            }
        )

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
            continue

        seen[key] = merge_duplicate_event_records(seen[key], item)

    return list(seen.values())


def normalize_key_text(value):
    text = repair_text_encoding(value or "").lower().strip()
    text = re.sub(r"[\s\-–—・:：!！?？\"'“”‘’「」『』（）()\[\]【】／/.,]+", "", text)
    return text


def build_dedupe_key(item):
    category = repair_text_encoding(item.get("category", "")).lower()

    if category == "film":
        title_key = normalize_key_text(item.get("title", ""))
        if title_key:
            return f"film::{title_key}"

    if category == "nightlife":
        title_key = normalize_key_text(item.get("title", ""))
        venue_key = normalize_key_text(item.get("venue") or item.get("location", ""))
        start_key = repair_text_encoding(item.get("startDate", "")).strip() or normalize_key_text(item.get("date", ""))
        if title_key and venue_key and start_key:
            return f"nightlife::{title_key}::{venue_key}::{start_key}"

    return item.get("sourceUrl") or item.get("slug") or str(item.get("id"))


def combine_unique_strings(*values):
    results = []
    seen = set()

    for value in values:
        if not value:
            continue
        text = repair_text_encoding(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        results.append(text)

    return results


def merge_screening_venues(existing, incoming):
    results = []
    seen = set()

    for venue in (existing or []) + (incoming or []):
        name = repair_text_encoding(venue.get("name", "")).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        results.append(
            {
                "name": name,
                "code": repair_text_encoding(venue.get("code", "")).strip(),
                "url": repair_text_encoding(venue.get("url", "")).strip(),
            }
        )

    return results


def build_screening_summary(venues):
    names = [venue.get("name", "").strip() for venue in venues if venue.get("name", "").strip()]
    if not names:
        return "Selected Tokyo cinemas"
    if len(names) <= 3:
        return ", ".join(names)
    return f"{', '.join(names[:3])} + {len(names) - 3} more"


def pick_preferred_url(existing, incoming):
    preferred_domains = ("entershibuya.com", "tohotheater.jp", "109cinemas.net")

    for candidate in [incoming, existing]:
        if any(domain in (candidate or "") for domain in preferred_domains):
            return candidate

    return incoming or existing


def pick_preferred_text(existing, incoming):
    existing_text = repair_text_encoding(existing or "").strip()
    incoming_text = repair_text_encoding(incoming or "").strip()

    if not existing_text:
        return incoming_text
    if not incoming_text:
        return existing_text

    return incoming_text if len(incoming_text) > len(existing_text) else existing_text


def merge_duplicate_event_records(existing, incoming):
    category = repair_text_encoding(existing.get("category", "")).lower()

    if category == "film":
        merged = dict(existing)
        merged["source"] = ", ".join(combine_unique_strings(existing.get("source", ""), incoming.get("source", "")))
        merged["title"] = pick_preferred_text(existing.get("title", ""), incoming.get("title", ""))
        merged["image"] = incoming.get("image") if has_real_image(incoming) and not has_real_image(existing) else existing.get("image") or incoming.get("image", "")
        merged["director"] = pick_preferred_text(existing.get("director", ""), incoming.get("director", ""))
        merged["cast"] = pick_preferred_text(existing.get("cast", ""), incoming.get("cast", ""))
        merged["sourceUrl"] = pick_preferred_url(existing.get("sourceUrl", ""), incoming.get("sourceUrl", ""))
        merged["bookingUrl"] = pick_preferred_url(existing.get("bookingUrl", ""), incoming.get("bookingUrl", ""))
        merged["screeningVenues"] = merge_screening_venues(existing.get("screeningVenues", []), incoming.get("screeningVenues", []))
        merged["location"] = build_screening_summary(merged["screeningVenues"])
        merged["access"] = ", ".join(venue["name"] for venue in merged["screeningVenues"])
        merged["venue"] = "Tokyo major cinemas"
        merged["tags"] = combine_unique_strings(*(existing.get("tags", []) + incoming.get("tags", [])))
        merged["rawDescription"] = combine_unique_strings(*(existing.get("rawDescription", []) + incoming.get("rawDescription", [])))[:5]
        return merged

    if category == "nightlife":
        merged = dict(existing)
        official_url = pick_preferred_url(existing.get("sourceUrl", ""), incoming.get("sourceUrl", ""))
        merged_source = existing.get("source", "")
        if "entershibuya.com" in (incoming.get("sourceUrl", "") or ""):
            merged_source = incoming.get("source", "") or merged_source
        merged["title"] = pick_preferred_text(existing.get("title", ""), incoming.get("title", ""))
        merged["image"] = incoming.get("image") if has_real_image(incoming) and not has_real_image(existing) else existing.get("image") or incoming.get("image", "")
        merged["date"] = pick_preferred_text(existing.get("date", ""), incoming.get("date", ""))
        merged["location"] = pick_preferred_text(existing.get("location", ""), incoming.get("location", ""))
        merged["venue"] = pick_preferred_text(existing.get("venue", ""), incoming.get("venue", ""))
        merged["price"] = pick_preferred_text(existing.get("price", ""), incoming.get("price", ""))
        merged["source"] = merged_source
        merged["sourceUrl"] = official_url
        merged["bookingUrl"] = pick_preferred_url(existing.get("bookingUrl", ""), incoming.get("bookingUrl", ""))
        merged["tags"] = combine_unique_strings(*(existing.get("tags", []) + incoming.get("tags", [])))
        merged["rawDescription"] = combine_unique_strings(*(existing.get("rawDescription", []) + incoming.get("rawDescription", [])))[:5]
        return merged

    return existing


def has_real_image(item):
    image = repair_text_encoding(item.get("image", "")).strip().lower()
    if not image:
        return False

    return not any(pattern in image for pattern in PLACEHOLDER_IMAGE_PATTERNS)


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
        sompo_exhibitions = []
        artizon_exhibitions = []
        momat_exhibitions = []
        nmwa_exhibitions = []
        designsight_exhibitions = []
        mot_exhibitions = []
        tnm_exhibitions = []
        nact_exhibitions = []
        film_events = []
        film_events_109 = []
        clubberia_nightlife = []
        enter_nightlife = []
        gotokyo_activities = []

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
            print("before sompo exhibitions")
            sompo_exhibitions = fetch_sompo_exhibitions()
            print("after sompo exhibitions:", len(sompo_exhibitions))
        except Exception as e:
            print("[SOMPO] failed:", e)

        try:
            print("before artizon exhibitions")
            artizon_exhibitions = fetch_artizon_exhibitions()
            print("after artizon exhibitions:", len(artizon_exhibitions))
        except Exception as e:
            print("[ARTIZON] failed:", e)

        try:
            print("before momat exhibitions")
            momat_exhibitions = fetch_momat_exhibitions()
            print("after momat exhibitions:", len(momat_exhibitions))
        except Exception as e:
            print("[MOMAT] failed:", e)

        try:
            print("before nmwa exhibitions")
            nmwa_exhibitions = fetch_nmwa_exhibitions()
            print("after nmwa exhibitions:", len(nmwa_exhibitions))
        except Exception as e:
            print("[NMWA] failed:", e)

        try:
            print("before 2121 exhibitions")
            designsight_exhibitions = fetch_2121_exhibitions()
            print("after 2121 exhibitions:", len(designsight_exhibitions))
        except Exception as e:
            print("[2121] failed:", e)

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

        try:
            print("before film events")
            film_events = fetch_toho_now_showing_films()
            print("after film events:", len(film_events))
        except Exception as e:
            print("[TOHO FILM] failed:", e)

        try:
            print("before 109 film events")
            film_events_109 = fetch_109_now_showing_films()
            print("after 109 film events:", len(film_events_109))
        except Exception as e:
            print("[109 FILM] failed:", e)

        try:
            print("before clubberia nightlife")
            clubberia_nightlife = fetch_clubberia_nightlife()
            print("after clubberia nightlife:", len(clubberia_nightlife))
        except Exception as e:
            print("[CLUBBERIA] failed:", e)

        try:
            print("before ENTER nightlife")
            enter_nightlife = fetch_enter_nightlife()
            print("after ENTER nightlife:", len(enter_nightlife))
        except Exception as e:
            print("[ENTER] failed:", e)

        try:
            print("before gotokyo activities")
            gotokyo_activities = fetch_gotokyo_activities()
            print("after gotokyo activities:", len(gotokyo_activities))
        except Exception as e:
            print("[GOTOKYO] failed:", e)

        merged_exhibitions = merge_exhibitions(
            mori_exhibitions,
            tobikan_exhibitions,
            sompo_exhibitions,
            artizon_exhibitions,
            momat_exhibitions,
            nmwa_exhibitions,
            designsight_exhibitions,
            mot_exhibitions,
            tnm_exhibitions,
            nact_exhibitions,
        )

        print("merged exhibitions:", len(merged_exhibitions))

        all_events.extend(merged_exhibitions)
        all_events.extend(film_events)
        all_events.extend(film_events_109)
        all_events.extend(clubberia_nightlife)
        all_events.extend(enter_nightlife)
        all_events.extend(gotokyo_activities)
        all_events = [normalize_raw_event(item) for item in all_events]
        all_events = [item for item in all_events if has_real_image(item)]
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
