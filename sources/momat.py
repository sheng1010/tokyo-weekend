import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.common_utils import normalize_text
from utils.http_utils import create_session
from utils.score_utils import calculate_exhibition_score


BASE_URL = "https://www.momat.go.jp/en/exhibitions"
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


def clean_title(text: str) -> str:
    cleaned = normalize_space(text)
    cleaned = cleaned.replace("|", ": ")
    cleaned = cleaned.replace("〞", " - ")
    cleaned = cleaned.replace("〟", " - ")
    cleaned = re.sub(r"[\u3100-\u312f]+", "", cleaned).strip()
    if cleaned.startswith("MOMAT Collection"):
        return "MOMAT Collection"
    return cleaned


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
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{1,2})(?:,\s*(\d{4}))?\s*-\s*"
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        r"(\d{1,2})(?:,\s*(\d{4}))?",
        cleaned,
    )
    if not match:
        return "", ""

    start_month, start_day, start_year, end_month, end_day, end_year = match.groups()
    final_end_year = end_year or start_year
    final_start_year = start_year or final_end_year

    start_date = to_iso_date(start_month, start_day, final_start_year or "")
    end_date = to_iso_date(end_month, end_day, final_end_year or "")
    return start_date, end_date


def fetch_momat_detail(session, detail_url: str):
    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[MOMAT] Detail fetch failed: {detail_url} | {exc}")
        return {}

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    title_node = soup.select_one("h1.ja-title")
    og_image = soup.find("meta", attrs={"property": "og:image"})

    title = clean_title(title_node.get_text(" ", strip=True)) if title_node else ""
    image = urljoin(detail_url, og_image["content"]) if og_image and og_image.get("content") else ""
    if "MomatLogo" in image:
        image = ""

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
                "admission",
                "ticket",
                "campus members",
                "same-day tickets",
                "hours",
                "closed",
                "share",
                "copyright",
                "display period",
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


def fetch_momat_exhibitions(start_id=14201):
    session = create_session()
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date().isoformat()

    try:
        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[MOMAT] Listing fetch failed: {exc}")
        return []

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen_titles = set()
    next_id = start_id

    for card in soup.select("section.item"):
        link = card.select_one('a[href*="/en/exhibitions/"]')
        if not link:
            continue

        href = urljoin(BASE_URL, link.get("href", ""))
        listing_text = normalize_space(link.get_text(" ", strip=True))
        date_match = re.search(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?\s*-\s*"
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*\d{4})?",
            listing_text,
        )
        date_text = date_match.group(0) if date_match else ""
        start_date, end_date = parse_date_range(date_text)
        if end_date and end_date < today:
            continue

        detail = fetch_momat_detail(session, href)
        title = detail.get("title", "")
        if not title:
            continue

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
            "location": "The National Museum of Modern Art, Tokyo (Takebashi)",
            "venue": "The National Museum of Modern Art, Tokyo",
            "date": date_text or "See source",
            "startDate": start_date,
            "endDate": end_date,
            "image": detail.get("image", ""),
            "access": "Takebashi Station (Tozai Line), around 3 minutes on foot",
            "price": "",
            "bookingUrl": "",
            "source": "The National Museum of Modern Art, Tokyo",
            "sourceUrl": href,
            "tags": [],
            "area": "Takebashi",
            "language": "en",
            "rawDescription": raw_description,
            "sources": ["The National Museum of Modern Art, Tokyo"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "score": 0,
        }
        entry["score"] = calculate_exhibition_score(entry)

        results.append(entry)
        print(f"[MOMAT] Added exhibition #{next_id}: {title}")
        next_id += 1

    print(f"[MOMAT] Total exhibitions collected: {len(results)}")
    return results
