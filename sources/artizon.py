import re
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.common_utils import normalize_text
from utils.http_utils import create_session
from utils.score_utils import calculate_exhibition_score


BASE_URL = "https://www.artizon.museum/en/exhibition/schedule"
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


def parse_single_date(month_name: str, day: str, year: str):
    month = MONTH_MAP.get(month_name)
    if not month:
        return ""
    return f"{int(year):04d}-{month:02d}-{int(day):02d}"


def parse_date_range(text: str):
    cleaned = normalize_space(text)
    matches = re.findall(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s+\[[A-Za-z.]+\],?\s+(\d{4})", cleaned)
    if not matches:
        return "", ""

    start = parse_single_date(*matches[0])
    end = start
    if len(matches) > 1:
        end = parse_single_date(*matches[1])

    return start, end


def fetch_artizon_detail(session, detail_url: str):
    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[ARTIZON] Detail fetch failed: {detail_url} | {exc}")
        return {}

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    title_nodes = soup.select(".subPageTitleH1")
    title = ""
    subtitle = ""
    if title_nodes:
        if len(title_nodes) == 1:
            title = normalize_space(title_nodes[0].get_text(" ", strip=True))
        else:
            subtitle = normalize_space(title_nodes[0].get_text(" ", strip=True))
            title = normalize_space(title_nodes[1].get_text(" ", strip=True))

    date_node = soup.select_one(".exhibitionPostDate")
    date_text = normalize_space(date_node.get_text(" ", strip=True)) if date_node else ""

    image = ""
    for image_tag in soup.select(".main img.protect, .contents img.protect"):
        src = image_tag.get("src", "").strip()
        if src.startswith("https://atz-image"):
            image = src
            break

    description = ""
    for case in soup.select(".contents .case"):
        text = normalize_space(case.get_text(" ", strip=True))
        if not text:
            continue
        if "About this exhibition" not in text:
            continue
        description = text.split("About this exhibition", 1)[-1].strip()
        description = description.split("Exhibition overview", 1)[0].strip()
        break

    raw_description = []
    if description:
        raw_description = [
            segment.strip()
            for segment in re.split(r"(?<=[.!?])\s+", description)
            if segment.strip()
        ][:4]

    return {
        "title": title,
        "subtitle": subtitle,
        "date": date_text,
        "startDate": "",
        "endDate": "",
        "image": image,
        "rawDescription": raw_description,
    }


def fetch_artizon_exhibitions(start_id=14101):
    session = create_session()
    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date().isoformat()

    try:
        response = session.get(BASE_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[ARTIZON] Listing fetch failed: {exc}")
        return []

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    seen_titles = set()
    next_id = start_id

    for block in soup.select(".eventBlock"):
        date_node = block.select_one(".eventBlock__TitleH3")
        if not date_node:
            continue

        date_text = normalize_space(date_node.get_text(" ", strip=True))
        start_date, end_date = parse_date_range(date_text)

        if end_date and end_date < today:
            continue

        for link in block.select('.eventBlock__col-3_wrap a[href*="/en/exhibition/detail/"]'):
            href = urljoin(BASE_URL, link.get("href", ""))
            title = normalize_space(link.get_text(" ", strip=True))

            if not title:
                continue

            key = normalize_text(title)
            if key in seen_titles:
                continue
            seen_titles.add(key)

            detail = fetch_artizon_detail(session, href)
            final_title = detail.get("title") or title
            raw_description = detail.get("rawDescription") or [final_title]

            entry = {
                "id": next_id,
                "slug": make_slug(final_title),
                "title": final_title,
                "category": "Exhibition",
                "location": "Artizon Museum (Kyobashi)",
                "venue": "Artizon Museum",
                "date": detail.get("date") or date_text or "See source",
                "startDate": start_date,
                "endDate": end_date,
                "image": detail.get("image", ""),
                "access": "Kyobashi Station / Tokyo Station area",
                "price": "",
                "bookingUrl": "",
                "source": "Artizon Museum",
                "sourceUrl": href,
                "tags": [],
                "area": "Kyobashi",
                "language": "en",
                "rawDescription": raw_description,
                "sources": ["Artizon Museum"],
                "popularity": 0,
                "bookmarkCount": 0,
                "wentCount": 0,
                "commentCount": 0,
                "score": 0,
            }
            entry["score"] = calculate_exhibition_score(entry)

            results.append(entry)
            print(f"[ARTIZON] Added exhibition #{next_id}: {final_title}")
            next_id += 1

    print(f"[ARTIZON] Total exhibitions collected: {len(results)}")
    return results
