import html
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.http_utils import create_session


MONTH_MAP = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def fetch_nfaj_films(start_id=11001):
    base_url = "https://www.nfaj.go.jp"
    home_url = f"{base_url}/english/"
    print(f"[NFAJ] Fetching {home_url}")

    session = create_session()

    try:
        response = session.get(home_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[NFAJ] Error fetching homepage: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
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

    def extract_date_range(date_text: str):
        date_text = normalize_space(date_text)
        year_match = re.findall(r"(20\d{2})", date_text)
        default_year = int(year_match[-1]) if year_match else None
        matches = re.findall(
            r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:,\s*(20\d{2}))?",
            date_text,
            flags=re.IGNORECASE,
        )

        parsed = []
        for month_name, day, explicit_year in matches:
            year = int(explicit_year or default_year or 0)
            if not year:
                continue
            month = MONTH_MAP[month_name.lower()]
            parsed.append(f"{year:04d}-{month:02d}-{int(day):02d}")

        if not parsed:
            return "", ""

        return parsed[0], parsed[-1]

    def extract_between(text: str, start_label: str, end_label: str) -> str:
        pattern = rf"{re.escape(start_label)}\s+(.+?)\s+{re.escape(end_label)}"
        match = re.search(pattern, text, flags=re.DOTALL)
        return normalize_space(match.group(1)) if match else ""

    def clean_date_text(date_text: str) -> str:
        date_text = normalize_space(date_text)
        replacements = {
            "–": " - ",
            "—": " - ",
            "每": " - ",
            "毎": " - ",
        }

        for old, new in replacements.items():
            date_text = date_text.replace(old, new)

        return normalize_space(date_text)

    def fetch_detail(detail_url: str):
        try:
            resp = session.get(detail_url, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[NFAJ] Detail fetch failed: {detail_url} | {exc}")
            return {}

        detail_soup = BeautifulSoup(resp.text, "html.parser")
        full_text = normalize_space(detail_soup.get_text(" ", strip=True))

        title_tag = detail_soup.find("h1")
        title = normalize_space(title_tag.get_text(" ", strip=True)) if title_tag else ""

        raw_paragraphs = []
        for p in detail_soup.find_all("p"):
            text = normalize_space(p.get_text(" ", strip=True))
            lower = text.lower()
            if len(text) < 40:
                continue
            if any(
                bad in lower
                for bad in [
                    "ticket information",
                    "assigned seating",
                    "box office",
                    "copyright",
                    "please see this page",
                    "hello dial",
                ]
            ):
                continue
            if text not in raw_paragraphs:
                raw_paragraphs.append(text)

        date_text = clean_date_text(extract_between(full_text, "Date", "Location"))
        venue = extract_between(full_text, "Location", "Capacity") or "National Film Archive of Japan"
        start_date, end_date = extract_date_range(date_text)

        image = ""
        og_image = detail_soup.find("meta", attrs={"property": "og:image"})
        if og_image:
            image = normalize_space(og_image.get("content", ""))

        return {
            "title": title,
            "date": date_text,
            "venue": venue,
            "image": image,
            "startDate": start_date,
            "endDate": end_date,
            "rawDescription": raw_paragraphs[:4],
        }

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        if "/english/film-program/" not in href:
            continue

        detail_url = make_absolute(href)
        if detail_url in seen_urls:
            continue

        seen_urls.add(detail_url)
        detail = fetch_detail(detail_url)
        title = detail.get("title") or normalize_space(anchor.get_text(" ", strip=True))
        if not title or title.lower() in {"no film programs", "film programs"}:
            continue

        record = {
            "id": next_id,
            "slug": make_slug(title),
            "title": title,
            "category": "Film",
            "location": detail.get("venue") or "Nagase Memorial Theatre OZU",
            "venue": "National Film Archive of Japan",
            "date": detail.get("date") or "See source",
            "startDate": detail.get("startDate", ""),
            "endDate": detail.get("endDate", ""),
            "image": detail.get("image", ""),
            "access": "See the official program page for screening dates and tickets",
            "price": "",
            "bookingUrl": detail_url,
            "source": "National Film Archive of Japan",
            "sourceUrl": detail_url,
            "tags": ["film", "screening", "program"],
            "area": "Kyobashi",
            "language": "en",
            "rawDescription": detail.get("rawDescription") or [title],
        }

        results.append(record)
        print(f"[NFAJ] Added film #{next_id}: {title}")
        next_id += 1

    return results
