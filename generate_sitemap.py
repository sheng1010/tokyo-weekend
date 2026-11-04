"""Write sitemap.xml for pages and listings that are still current.

Uses the same visibility rules as Js/main.js:
- skip events whose endDate is before today
- skip films that have no end date and are labeled only as now showing
- skip entries without a real image
"""

import json
import re
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

MONTHS = {
    name.lower(): index
    for index, name in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}

ROOT = Path(__file__).resolve().parent
EVENTS_PATH = ROOT / "data" / "generated_events.json"
OUTPUT_PATH = ROOT / "sitemap.xml"
SITE = "https://tokyo-weekend.vercel.app"

STATIC_PATHS = [
    "/",
    "/pages/all.html",
    "/pages/film.html",
    "/pages/exhibitions.html",
    "/pages/nightlife.html",
    "/pages/activities.html",
    "/pages/about.html",
    "/pages/contact.html",
]


def parse_iso(value):
    text = str(value or "").strip()
    parts = text.split("-")
    if len(parts) != 3:
        return None
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return None


def parse_chunk(chunk, fallback_year=None):
    text = str(chunk or "").strip()
    dotted = re.search(r"(\d{4})\.(\d{1,2})\.(\d{1,2})", text)
    if dotted:
        return date(int(dotted.group(1)), int(dotted.group(2)), int(dotted.group(3)))

    short = re.search(r"(?<!\d)(\d{1,2})\.(\d{1,2})(?!\d)", text)
    if short and fallback_year:
        return date(fallback_year, int(short.group(1)), int(short.group(2)))

    named = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?(?:\s*\([^)]*\))?(?:,)?\s*(\d{4})?",
        text,
        flags=re.IGNORECASE,
    )
    if not named:
        return None
    year = int(named.group(3)) if named.group(3) else fallback_year
    if not year:
        return None
    return date(year, MONTHS[named.group(1).lower()], int(named.group(2)))


def parse_display_range(text):
    raw = str(text or "").strip()
    lower = raw.lower()
    if not raw or lower in {"see source", "now showing"}:
        return None, None
    parts = re.split(r"\s*[–—-]\s*", raw)
    years = [int(year) for year in re.findall(r"\d{4}", raw)]
    fallback = years[0] if years else None
    if len(parts) == 1:
        return None, parse_chunk(parts[0], fallback)
    start = parse_chunk(parts[0], fallback)
    end = parse_chunk(parts[-1], start.year if start else (years[-1] if years else None))
    if start and end and end < start and not re.search(r"\d{4}", parts[-1]):
        end = date(end.year + 1, end.month, end.day)
    return start, end


def effective_end(item):
    iso_end = parse_iso(item.get("endDate"))
    if iso_end or parse_iso(item.get("startDate")):
        return iso_end
    return parse_display_range(item.get("date"))[1]


def has_real_image(item):
    image = str(item.get("image") or "").strip().lower()
    if not image:
        return False
    blocked = ("no_image", "noimage", "sakuhin_nothing", "comingsoon_noimg")
    return not any(pattern in image for pattern in blocked)


def is_listable(item, today):
    if not has_real_image(item):
        return False
    end = effective_end(item)
    if end and end < today:
        return False
    if str(item.get("category") or "").lower() == "film" and parse_iso(item.get("endDate")) is None:
        label = str(item.get("date") or "").strip().lower()
        if label in {"", "now showing"}:
            return False
    return True


def main():
    today = date.today()
    events = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
    urls = list(STATIC_PATHS)
    for item in events:
        if not is_listable(item, today):
            continue
        slug = str(item.get("slug") or "").strip()
        if not slug:
            continue
        urls.append(f"/event/{slug}")

    body = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for path in urls:
        body.append("  <url>")
        body.append(f"    <loc>{escape(SITE + path)}</loc>")
        body.append("  </url>")
    body.append("</urlset>")
    body.append("")
    OUTPUT_PATH.write_text("\n".join(body), encoding="utf-8")
    print(f"Wrote {len(urls)} urls to {OUTPUT_PATH.name}")


if __name__ == "__main__":
    main()
