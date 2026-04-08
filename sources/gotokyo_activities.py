import html
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.http_utils import create_session


def fetch_gotokyo_activities(start_id=13001):
    base_url = "https://www.gotokyo.org"
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

    def extract_json_ld(soup: BeautifulSoup) -> dict:
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            raw = script.get_text(strip=True)
            if not raw:
                continue

            try:
                data = json.loads(raw)
            except Exception:
                continue

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Event":
                        return item
            elif isinstance(data, dict) and data.get("@type") == "Event":
                return data

        return {}

    def extract_access_text(full_text: str) -> str:
        match = re.search(r"How to Get There\s+(.+?)\s+Keywords", full_text, flags=re.DOTALL)
        return normalize_space(match.group(1)) if match else ""

    def fetch_detail(detail_url: str):
        try:
            response = session.get(detail_url, timeout=20)
            response.raise_for_status()
        except Exception as exc:
            print(f"[GOTOKYO] Detail fetch failed: {detail_url} | {exc}")
            return {}

        soup = BeautifulSoup(response.text, "html.parser")
        data = extract_json_ld(soup)
        full_text = normalize_space(soup.get_text(" ", strip=True))

        name = normalize_space(html.unescape(data.get("name", "")))
        description = normalize_space(html.unescape(data.get("description", "")))

        location_data = data.get("location", {}) or {}
        address_data = location_data.get("address", {}) or {}
        location_name = normalize_space(html.unescape(address_data.get("name", "")))

        image = data.get("image", [])
        if isinstance(image, list):
            image = image[0] if image else ""

        start_date = normalize_space(data.get("startDate", ""))
        end_date = normalize_space(data.get("endDate", "")) or start_date

        return {
            "title": name,
            "description": description,
            "location": location_name,
            "image": normalize_space(image),
            "startDate": start_date,
            "endDate": end_date,
            "access": extract_access_text(full_text),
        }

    keywords = ["Spring", "Cherry Blossom"]

    for keyword in keywords:
        list_url = (
            "https://www.gotokyo.org/en/travel-directory/result/index/"
            f"keyword/{keyword.replace(' ', '%20')}/template/153"
        )
        print(f"[GOTOKYO] Fetching {list_url}")

        try:
            response = session.get(list_url, timeout=30)
            response.raise_for_status()
        except Exception as exc:
            print(f"[GOTOKYO] Error fetching list page: {exc}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if "/en/spot/ev" not in href:
                continue

            detail_url = make_absolute(href)
            if detail_url in seen_urls:
                continue

            seen_urls.add(detail_url)
            detail = fetch_detail(detail_url)
            title = detail.get("title", "")
            if not title:
                continue

            if "film festival" in title.lower():
                continue

            end_date = detail.get("endDate", "")
            if end_date and end_date < today.isoformat():
                continue

            start_date = detail.get("startDate", "")
            date_text = start_date
            if start_date and end_date and end_date != start_date:
                date_text = f"{start_date} - {end_date}"

            record = {
                "id": next_id,
                "slug": make_slug(title),
                "title": title,
                "category": "Activity",
                "location": detail.get("location") or "Tokyo",
                "venue": detail.get("location") or "Tokyo event",
                "date": date_text or "See source",
                "startDate": start_date,
                "endDate": end_date,
                "image": detail.get("image", ""),
                "access": detail.get("access", ""),
                "price": "",
                "bookingUrl": detail_url,
                "source": "GO TOKYO",
                "sourceUrl": detail_url,
                "tags": ["tokyo", "festival"],
                "area": "",
                "language": "en",
                "rawDescription": [detail.get("description")] if detail.get("description") else [title],
            }

            results.append(record)
            safe_title = title.encode("ascii", "ignore").decode() or title.encode("unicode_escape").decode()
            print(f"[GOTOKYO] Added activity #{next_id}: {safe_title}")
            next_id += 1

    return results
