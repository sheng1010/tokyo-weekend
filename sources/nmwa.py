import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.common_utils import normalize_text
from utils.http_utils import create_session
from utils.score_utils import calculate_exhibition_score


BASE_URL = "https://www.nmwa.go.jp/en/exhibitions/current.html"
LISTING_URLS = (
    "https://www.nmwa.go.jp/en/exhibitions/current.html",
    "https://www.nmwa.go.jp/en/exhibitions/upcoming.html",
)
MONTH_MAP = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def make_slug(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def to_iso_date(month_name: str, day: str, year: str) -> str:
    month = MONTH_MAP.get(month_name)
    if not month:
        return ""
    return f"{int(year):04d}-{month:02d}-{int(day):02d}"


def parse_date_range(text: str):
    cleaned = normalize_space(text).replace("–", "-").replace("—", "-")
    if not cleaned:
        return "", ""

    match = re.search(
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*"
        r"(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"(?:\s+(\d{4}))?\s*-\s*"
        r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s*"
        r"(\d{1,2})\s+"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+(\d{4})",
        cleaned,
    )
    if not match:
        return "", ""

    start_day, start_month, start_year, end_day, end_month, end_year = match.groups()
    final_start_year = start_year or end_year
    start_date = to_iso_date(start_month, start_day, final_start_year)
    end_date = to_iso_date(end_month, end_day, end_year)
    return start_date, end_date


def clean_heading(text: str) -> str:
    cleaned = normalize_space(text)
    prefixes = (
        "Current Exhibitions",
        "Upcoming Exhibitions",
        "Special Exhibition",
        "Exhibition",
        "The Collection",
    )
    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    return cleaned


def safe_log_text(text: str) -> str:
    return text.encode("ascii", errors="ignore").decode("ascii") or "untitled"


def fetch_nmwa_detail(session, detail_url: str):
    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[NMWA] Detail fetch failed: {detail_url} | {exc}")
        return {}

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    heading = soup.select_one("main h1")
    title = clean_heading(heading.get_text(" ", strip=True)) if heading else ""

    image = ""
    for image_tag in soup.select("img"):
        src = image_tag.get("src", "").strip()
        if "/exhibitions/img/" in src:
            image = urljoin(detail_url, src)
            break

    raw_description = []
    seen = set()
    for paragraph in soup.select("main p"):
        text = normalize_space(paragraph.get_text(" ", strip=True))
        lower = text.lower()
        if len(text) < 80:
            continue
        if any(
            bad in lower
            for bad in (
                "student id",
                "proof of age",
                "tickets",
                "ticket",
                "admission",
                "view this exhibition",
                "organizer",
                "venue",
            )
        ):
            continue
        if text in seen:
            continue
        seen.add(text)
        raw_description.append(text)
        if len(raw_description) >= 4:
            break

    return {
        "title": title,
        "image": image,
        "rawDescription": raw_description,
    }


def fetch_nmwa_exhibitions(start_id=14301):
    session = create_session()
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date().isoformat()

    results = []
    seen_titles = set()
    next_id = start_id

    for listing_url in LISTING_URLS:
        try:
            response = session.get(listing_url, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            print(f"[NMWA] Listing fetch failed: {listing_url} | {exc}")
            continue

        response.encoding = response.apparent_encoding or response.encoding
        soup = BeautifulSoup(response.text, "html.parser")

        for section in soup.select("section.exb_info"):
            link = section.select_one('a[href*="/en/exhibitions/"]')
            if not link:
                continue

            href = urljoin(BASE_URL, link.get("href", ""))
            if href.endswith(("current.html", "upcoming.html")) or "/past/" in href:
                continue

            section_text = normalize_space(section.get_text(" ", strip=True))
            title = section_text.split("Dates", 1)[0].strip()
            title = clean_heading(title)
            if not title:
                continue

            date_match = re.search(r"Dates\s+(.+?)\s+Venue\s+", section_text)
            venue_match = re.search(r"Venue\s+(.+?)\s+To details", section_text)
            date_text = date_match.group(1).strip() if date_match else ""
            listing_venue = venue_match.group(1).strip() if venue_match else ""
            start_date, end_date = parse_date_range(date_text)

            if end_date and end_date < today:
                continue

            detail = fetch_nmwa_detail(session, href)
            final_title = detail.get("title") or title
            key = normalize_text(final_title)
            if key in seen_titles:
                continue
            seen_titles.add(key)

            raw_description = detail.get("rawDescription") or [final_title]
            venue = "The National Museum of Western Art"
            if listing_venue:
                venue = f"{venue} - {listing_venue}"

            entry = {
                "id": next_id,
                "slug": make_slug(final_title),
                "title": final_title,
                "category": "Exhibition",
                "location": "The National Museum of Western Art (Ueno)",
                "venue": venue,
                "date": date_text or "See source",
                "startDate": start_date,
                "endDate": end_date,
                "image": detail.get("image", ""),
                "access": "Ueno Station / Keisei Ueno Station, around 1 to 7 minutes on foot",
                "price": "",
                "bookingUrl": "",
                "source": "The National Museum of Western Art",
                "sourceUrl": href,
                "tags": [],
                "area": "Ueno",
                "language": "en",
                "rawDescription": raw_description,
                "sources": ["The National Museum of Western Art"],
                "popularity": 0,
                "bookmarkCount": 0,
                "wentCount": 0,
                "commentCount": 0,
                "score": 0,
            }
            entry["score"] = calculate_exhibition_score(entry)

            results.append(entry)
            print(f"[NMWA] Added exhibition #{next_id}: {safe_log_text(final_title)}")
            next_id += 1

    print(f"[NMWA] Total exhibitions collected: {len(results)}")
    return results
