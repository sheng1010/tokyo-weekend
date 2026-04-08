import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.common_utils import normalize_text
from utils.http_utils import create_session
from utils.score_utils import calculate_exhibition_score


BASE_URL = "https://www.sompo-museum.org/en/exhibitions/"


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def make_slug(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def parse_date_range(text: str):
    cleaned = normalize_space(text)
    if not cleaned:
        return "", ""

    matches = re.findall(r"(\d{4})\.(\d{2})\.(\d{2})", cleaned)
    if not matches:
        return "", ""

    start = f"{matches[0][0]}-{matches[0][1]}-{matches[0][2]}"
    end = start
    if len(matches) > 1:
        end = f"{matches[1][0]}-{matches[1][1]}-{matches[1][2]}"

    return start, end


def fetch_sompo_detail(session, detail_url: str):
    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[SOMPO] Detail fetch failed: {detail_url} | {exc}")
        return {}

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    title_node = soup.select_one(".p-exhibitions-detail-data__title")
    subtitle_node = soup.select_one(".p-exhibitions-detail-data__subtitle")
    date_node = soup.select_one(".p-exhibitions-detail-data__date")
    summary_node = soup.select_one(".p-exhibitions-detail-summary__text")
    image_tag = soup.select_one('img[src*="img_ex_detail"]')
    og_image = soup.find("meta", attrs={"property": "og:image"})

    title = normalize_space(title_node.get_text(" ", strip=True)) if title_node else ""
    subtitle = normalize_space(subtitle_node.get_text(" ", strip=True)) if subtitle_node else ""
    date_text = normalize_space(date_node.get_text(" ", strip=True)) if date_node else ""
    summary = normalize_space(summary_node.get_text(" ", strip=True)) if summary_node else ""

    image = ""
    if image_tag and image_tag.get("src"):
        image = urljoin(detail_url, image_tag["src"])
    elif og_image and og_image.get("content"):
        image = urljoin(detail_url, og_image["content"])

    start_date, end_date = parse_date_range(date_text)

    return {
        "title": title,
        "subtitle": subtitle,
        "date": date_text,
        "startDate": start_date,
        "endDate": end_date,
        "summary": summary,
        "image": image,
    }


def fetch_sompo_exhibitions(start_id=14001):
    session = create_session()
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date().isoformat()

    try:
        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[SOMPO] Listing fetch failed: {exc}")
        return []

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    seen_titles = set()
    next_id = start_id

    detail_links = []
    for link in soup.select('a[href*="/en/exhibitions/20"]'):
        href = urljoin(BASE_URL, link.get("href", ""))
        if not href.endswith("/"):
            href = f"{href}/"
        if href not in detail_links:
            detail_links.append(href)

    for detail_url in detail_links:
        detail = fetch_sompo_detail(session, detail_url)
        title = detail.get("title", "")
        if not title:
            continue

        key = normalize_text(title)
        if key in seen_titles:
            continue
        seen_titles.add(key)

        end_date = detail.get("endDate", "")
        if end_date and end_date < today:
            continue

        raw_description = [detail.get("summary", "")] if detail.get("summary") else [title]

        entry = {
            "id": next_id,
            "slug": make_slug(title),
            "title": title,
            "category": "Exhibition",
            "location": "Sompo Museum of Art (Shinjuku)",
            "venue": "Sompo Museum of Art",
            "date": detail.get("date") or "See source",
            "startDate": detail.get("startDate", ""),
            "endDate": detail.get("endDate", ""),
            "image": detail.get("image", ""),
            "access": "Shinjuku Station west exit area, around 5 minutes on foot",
            "price": "",
            "bookingUrl": "",
            "source": "Sompo Museum of Art",
            "sourceUrl": detail_url,
            "tags": [],
            "area": "Shinjuku",
            "language": "en",
            "rawDescription": raw_description,
            "sources": ["Sompo Museum of Art"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "score": 0,
        }
        entry["score"] = calculate_exhibition_score(entry)

        results.append(entry)
        print(f"[SOMPO] Added exhibition #{next_id}: {title}")
        next_id += 1

    print(f"[SOMPO] Total exhibitions collected: {len(results)}")
    return results
