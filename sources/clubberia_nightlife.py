import html
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.http_utils import create_session


TOKYO_AREA_MAP = {
    "渋谷区": "Shibuya",
    "新宿区": "Shinjuku",
    "港区": "Minato",
    "目黒区": "Meguro",
    "世田谷区": "Setagaya",
    "中央区": "Chuo",
    "台東区": "Taito",
    "豊島区": "Toshima",
    "品川区": "Shinagawa",
    "杉並区": "Suginami",
}


def fetch_clubberia_nightlife(start_id=12001):
    base_url = "https://clubberia.com"
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()
    session = create_session()
    results = []
    seen_urls = set()
    next_id = start_id

    def normalize_space(text: str) -> str:
        return " ".join((text or "").split())

    def make_absolute(path: str) -> str:
        return urljoin(base_url, path) if path else ""

    def make_slug(text: str) -> str:
        text = (text or "").lower().strip()
        text = text.replace("&", " and ")
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"\s+", "-", text)
        text = re.sub(r"-+", "-", text)
        return text.strip("-")

    def infer_area(address: str) -> str:
        for key, area in TOKYO_AREA_MAP.items():
            if key in address:
                return area
        return "Tokyo"

    def is_tokyo_address(address: str) -> bool:
        if "東京都" in address or "Tokyo" in address:
            return True
        return any(key in address for key in TOKYO_AREA_MAP)

    def extract_field(text: str, start_label: str, end_label: str) -> str:
        pattern = rf"{re.escape(start_label)}\s*(.+?)\s*{re.escape(end_label)}"
        match = re.search(pattern, text, flags=re.DOTALL)
        return normalize_space(match.group(1)) if match else ""

    def fetch_detail(detail_url: str, fallback_title: str):
        try:
            response = session.get(detail_url, timeout=20)
            response.raise_for_status()
        except Exception as exc:
            print(f"[CLUBBERIA] Detail fetch failed: {detail_url} | {exc}")
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        full_text = normalize_space(soup.get_text(" ", strip=True))

        title_tag = soup.find("h1")
        raw_title = normalize_space(title_tag.get_text(" ", strip=True)) if title_tag else ""
        title = raw_title if raw_title and len(raw_title) > 4 else fallback_title
        if "@" in fallback_title and (
            title.lower() in {"view more", "events", "wednesday", "thursday", "friday", "saturday", "sunday"}
            or len(fallback_title) > len(title) + 8
        ):
            title = fallback_title

        description = ""
        for key in ["description", "og:description"]:
            if key == "description":
                tag = soup.find("meta", attrs={"name": key})
            else:
                tag = soup.find("meta", attrs={"property": key})
            if tag and tag.get("content"):
                description = normalize_space(html.unescape(tag["content"]))
                break

        image = ""
        image_tag = soup.find("meta", attrs={"property": "og:image"})
        if image_tag and image_tag.get("content"):
            image = normalize_space(image_tag["content"])

        date_value = extract_field(full_text, "DATE:", "OPEN:")
        open_value = extract_field(full_text, "OPEN:", "VENUE:")
        venue = extract_field(full_text, "VENUE:", "PRICE:")
        price = extract_field(full_text, "PRICE:", "LINE UP:")
        lineup = extract_field(full_text, "LINE UP:", "Facebook Twitter VENUES VIEW MORE")

        address = ""
        if venue:
            pattern = rf"VENUES VIEW MORE\s+{re.escape(venue)}\s+(.+?)\s+EVENT SCHEDULE"
            match = re.search(pattern, full_text, flags=re.DOTALL)
            if match:
                address = normalize_space(match.group(1))

        start_date = ""
        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", date_value)
        if date_match:
            start_date = date_match.group(1)

        return {
            "title": title,
            "date": date_value,
            "open": open_value,
            "venue": venue,
            "price": price,
            "address": address,
            "image": image,
            "description": description,
            "lineup": lineup,
            "startDate": start_date,
        }

    def collect_from_page(url: str):
        nonlocal next_id
        print(f"[CLUBBERIA] Fetching {url}")
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            print(f"[CLUBBERIA] Error fetching list page: {exc}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        for article in soup.select("article.c-post"):
            links = article.find_all("a", href=True)
            detail_href = ""
            fallback_title = ""

            for anchor in links:
                href = anchor.get("href", "")
                if "/ja/events/" not in href or href.rstrip("/").endswith("/ja/events"):
                    continue
                detail_href = href
                anchor_text = normalize_space(anchor.get_text(" ", strip=True))
                if len(anchor_text) > len(fallback_title):
                    fallback_title = anchor_text

            if not detail_href:
                continue

            detail_url = make_absolute(detail_href)
            if detail_url in seen_urls:
                continue

            seen_urls.add(detail_url)
            detail = fetch_detail(detail_url, fallback_title)
            address = detail.get("address", "")

            if not is_tokyo_address(address):
                continue

            start_date = detail.get("startDate", "")
            if start_date and start_date < today.isoformat():
                continue

            title = detail.get("title") or fallback_title
            if not title:
                continue
            if title.upper().startswith("VIEW MORE"):
                continue
            if " @ " in title:
                title = title.split(" @ ", 1)[0].strip()

            raw_description = []
            if detail.get("description"):
                raw_description.append(detail["description"])
            if detail.get("lineup"):
                raw_description.append(detail["lineup"])

            venue = detail.get("venue") or "Club event"
            area = infer_area(address)
            open_text = f" / {detail['open']}" if detail.get("open") else ""

            record = {
                "id": next_id,
                "slug": make_slug(title),
                "title": title,
                "category": "Nightlife",
                "location": f"{venue} ({area})" if area else venue,
                "venue": venue,
                "date": f"{detail.get('date', 'See source')}{open_text}",
                "startDate": start_date,
                "endDate": start_date,
                "image": detail.get("image", ""),
                "access": "",
                "price": detail.get("price", ""),
                "bookingUrl": detail_url,
                "source": "clubberia",
                "sourceUrl": detail_url,
                "tags": ["nightlife", "club"],
                "area": area,
                "language": "ja",
                "rawDescription": raw_description or [title],
            }

            results.append(record)
            print(f"[CLUBBERIA] Added nightlife #{next_id}: {title}")
            next_id += 1

        next_week_link = soup.find("a", string=re.compile("NEXT WEEK", re.IGNORECASE))
        if next_week_link and next_week_link.get("href"):
            return make_absolute(next_week_link["href"])

        return None

    next_page = collect_from_page("https://clubberia.com/ja/events/")
    if next_page:
        collect_from_page(next_page)

    return results
