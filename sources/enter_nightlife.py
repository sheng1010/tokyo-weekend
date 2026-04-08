import re
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from utils.http_utils import create_session


BASE_URL = "https://entershibuya.com/"
VENUE_NAME = "ENTER shibuya"
AREA_NAME = "Shibuya"
WEEKDAY_MAP = {
    "月": "MON",
    "火": "TUE",
    "水": "WED",
    "木": "THU",
    "金": "FRI",
    "土": "SAT",
    "日": "SUN",
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


def parse_event_date(date_text: str):
    match = re.search(r"([月火水木金土日])\s+(\d{1,2})\s+(\d{1,2})月\s+(\d{4})", date_text)
    if not match:
        return "", "See source"

    weekday_ja, day, month, year = match.groups()
    start_date = f"{year}-{int(month):02d}-{int(day):02d}"
    display = f"{start_date} {WEEKDAY_MAP.get(weekday_ja, '')}".strip()
    return start_date, display


def fetch_enter_detail(session, detail_url: str):
    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[ENTER] Detail fetch failed: {detail_url} | {exc}")
        return {}

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    title_node = soup.select_one(".event-head .ttl")
    date_node = soup.select_one(".event-head .date")
    intro_node = soup.select_one(".kv-detail-ttl")
    lineup_node = soup.select_one(".lineup")
    info_node = soup.select_one(".event-info")
    image_tag = soup.find("meta", attrs={"property": "og:image"})
    description_tag = soup.find("meta", attrs={"property": "og:description"})

    title = normalize_space(title_node.get_text(" ", strip=True)) if title_node else ""
    date_text = normalize_space(date_node.get_text(" ", strip=True)) if date_node else ""
    intro = normalize_space(intro_node.get_text(" ", strip=True)) if intro_node else ""
    lineup = normalize_space(lineup_node.get_text(" ", strip=True)) if lineup_node else ""
    event_info = normalize_space(info_node.get_text(" ", strip=True)) if info_node else ""
    image = image_tag.get("content", "").strip() if image_tag else ""
    description = description_tag.get("content", "").strip() if description_tag else ""

    start_date, display_date = parse_event_date(date_text)

    open_match = re.search(r"OPEN[: ]\s*([0-9]{1,2}:[0-9]{2})", event_info, flags=re.IGNORECASE)
    open_time = open_match.group(1) if open_match else ""
    date_value = f"{display_date} / {open_time}".strip(" /") if display_date else "See source"

    return {
        "title": title,
        "date": date_value,
        "startDate": start_date,
        "image": image,
        "description": description or intro,
        "intro": intro,
        "lineup": lineup,
        "eventInfo": event_info,
    }


def fetch_enter_nightlife(start_id=12101):
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()
    session = create_session()

    try:
        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[ENTER] Listing fetch failed: {exc}")
        return []

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen_urls = set()
    next_id = start_id

    for post in soup.select(".post"):
        link = post.find("a", href=True)
        if not link:
            continue

        detail_url = link["href"].strip()
        if not detail_url.startswith("https://entershibuya.com/schedule/"):
            continue
        if detail_url in seen_urls:
            continue

        seen_urls.add(detail_url)
        detail = fetch_enter_detail(session, detail_url)
        start_date = detail.get("startDate", "")

        if start_date and start_date < today.isoformat():
            continue

        title = detail.get("title", "")
        if not title:
            continue

        raw_description = [
            value
            for value in [
                detail.get("description", ""),
                detail.get("intro", ""),
                detail.get("lineup", ""),
                detail.get("eventInfo", ""),
            ]
            if value
        ]

        record = {
            "id": next_id,
            "slug": make_slug(f"enter-{title}"),
            "title": title,
            "category": "Nightlife",
            "location": f"{VENUE_NAME} ({AREA_NAME})",
            "venue": VENUE_NAME,
            "date": detail.get("date", "See source"),
            "startDate": start_date,
            "endDate": start_date,
            "image": detail.get("image", ""),
            "access": "",
            "price": "",
            "bookingUrl": detail_url,
            "source": "ENTER",
            "sourceUrl": detail_url,
            "tags": ["nightlife", "club", "enter", "shibuya"],
            "area": AREA_NAME,
            "language": "ja",
            "rawDescription": raw_description[:4] or [title],
        }

        results.append(record)
        safe_title = title.encode("ascii", errors="backslashreplace").decode("ascii")
        print(f"[ENTER] Added nightlife #{next_id}: {safe_title}")
        next_id += 1

    return results
