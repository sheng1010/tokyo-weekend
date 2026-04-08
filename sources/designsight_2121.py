import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.common_utils import normalize_text
from utils.http_utils import create_session
from utils.score_utils import calculate_exhibition_score


BASE_URL = "https://www.2121designsight.jp/en/program/"
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
    cleaned = normalize_space(text)
    match = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{1,2})(?:\s+\([A-Za-z]{3}\))?,\s*(\d{4})\s*-\s*"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{1,2})(?:\s+\([A-Za-z]{3}\))?,\s*(\d{4})",
        cleaned,
    )
    if not match:
        return "", ""

    start_month, start_day, start_year, end_month, end_day, end_year = match.groups()
    start_date = to_iso_date(start_month, start_day, start_year)
    end_date = to_iso_date(end_month, end_day, end_year)
    return start_date, end_date


def extract_title_from_title_tag(text: str) -> str:
    parts = [part.strip() for part in (text or "").split("|")]
    if len(parts) >= 3:
        return parts[1]
    return parts[0] if parts else ""


def fetch_2121_detail(session, detail_url: str):
    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[2121] Detail fetch failed: {detail_url} | {exc}")
        return {}

    html = response.content.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    title = extract_title_from_title_tag(soup.title.get_text(" ", strip=True) if soup.title else "")

    image = ""
    for image_tag in soup.select('img[src*="/en/program/"]'):
        src = image_tag.get("src", "").strip()
        if src.endswith("topweb.jpg"):
            image = urljoin(detail_url, src)
            break
        if not image and src.endswith("header.jpg"):
            image = urljoin(detail_url, src)

    raw_description = []
    seen = set()
    for paragraph in soup.select(".clmBody p"):
        text = normalize_space(paragraph.get_text(" ", strip=True))
        lower = text.lower()
        if len(text) < 80:
            continue
        if any(
            bad in lower
            for bad in (
                "download the exhibition flyer",
                "general ¥",
                "general â¥",
                "university students",
                "junior high school students",
                "agency for cultural affairs",
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


def fetch_2121_exhibitions(start_id=14401):
    session = create_session()
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date().isoformat()

    try:
        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[2121] Listing fetch failed: {exc}")
        return []

    html = response.content.decode("utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    results = []
    seen_titles = set()
    next_id = start_id

    for link in soup.select('div.clmBox a[href*="/en/program/"]'):
        card = link.find_parent("div", class_="clmBox")
        listing_text = normalize_space(card.get_text(" ", strip=True)) if card else ""
        if not listing_text:
            continue

        href = urljoin(BASE_URL, link.get("href", ""))
        date_match = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\s*-\s*"
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
            listing_text,
        )
        if not date_match:
            date_match = re.search(
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s+\([A-Za-z]{3}\),\s+\d{4}\s*-\s*"
                r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}\s+\([A-Za-z]{3}\),\s+\d{4}",
                listing_text,
            )
        date_text = date_match.group(0) if date_match else ""
        if not date_text:
            continue
        start_date, end_date = parse_date_range(date_text)
        if end_date and end_date < today:
            continue

        detail = fetch_2121_detail(session, href)
        title = detail.get("title", "")
        if not title:
            title = listing_text
            title = re.sub(r"^NEW\s+\[(?:Current|Upcoming) Program\]\s*", "", title)
            if date_text:
                title = title.replace(date_text, "").strip()

        key = normalize_text(title)
        if key in seen_titles:
            continue
        seen_titles.add(key)

        raw_description = detail.get("rawDescription") or [title]

        entry = {
            "id": next_id,
            "slug": make_slug(title),
            "title": title,
            "category": "Exhibition",
            "location": "21_21 DESIGN SIGHT (Roppongi / Midtown)",
            "venue": "21_21 DESIGN SIGHT",
            "date": date_text or "See source",
            "startDate": start_date,
            "endDate": end_date,
            "image": detail.get("image", ""),
            "access": "Roppongi Station / Nogizaka Station, around 5 minutes on foot",
            "price": "",
            "bookingUrl": "",
            "source": "21_21 DESIGN SIGHT",
            "sourceUrl": href,
            "tags": [],
            "area": "Roppongi",
            "language": "en",
            "rawDescription": raw_description,
            "sources": ["21_21 DESIGN SIGHT"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "score": 0,
        }
        entry["score"] = calculate_exhibition_score(entry)

        results.append(entry)
        print(f"[2121] Added exhibition #{next_id}: {title}")
        next_id += 1

    print(f"[2121] Total exhibitions collected: {len(results)}")
    return results
