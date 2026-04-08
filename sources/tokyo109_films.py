import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from utils.http_utils import create_session


NOW_SHOWING_URL = "https://109cinemas.net/nowshowing/?vm=r"
BASE_URL = "https://109cinemas.net"
TOKYO_THEATERS = {
    "109シネマズプレミアム新宿": {
        "name": "109 Cinemas Premium Shinjuku",
        "url": "https://109cinemas.net/premiumshinjuku/",
    },
    "木場": {
        "name": "109 Cinemas Kiba",
        "url": "https://109cinemas.net/kiba/",
    },
    "二子玉川": {
        "name": "109 Cinemas Futako-Tamagawa",
        "url": "https://109cinemas.net/futako/",
    },
    "グランベリーパーク": {
        "name": "109 Cinemas Grandberry Park",
        "url": "https://109cinemas.net/grandberrypark/",
    },
}
IMPORTANT_THEATER_ORDER = [
    "109シネマズプレミアム新宿",
    "木場",
    "二子玉川",
    "グランベリーパーク",
]


def normalize_space(text: str) -> str:
    return " ".join((text or "").split())


def make_slug(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def split_synopsis(text: str):
    cleaned = normalize_space(text)
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[。！？.!?])\s*", cleaned)
    sentences = [normalize_space(sentence) for sentence in sentences if normalize_space(sentence)]
    if len(sentences) <= 2:
        return sentences

    parts = []
    current = []
    for sentence in sentences:
        current.append(sentence)
        joined = " ".join(current)
        if len(joined) >= 120:
            parts.append(joined)
            current = []

    if current:
        parts.append(" ".join(current))

    return parts[:3]


def score_theater_priority(raw_name: str) -> int:
    try:
        return IMPORTANT_THEATER_ORDER.index(raw_name)
    except ValueError:
        return len(IMPORTANT_THEATER_ORDER) + 1


def pick_tokyo_theaters(raw_theater_names):
    seen = set()
    results = []

    for raw_name in raw_theater_names:
        if raw_name not in TOKYO_THEATERS or raw_name in seen:
            continue

        theater = TOKYO_THEATERS[raw_name]
        results.append(
            {
                "name": theater["name"],
                "code": raw_name,
                "url": theater["url"],
            }
        )
        seen.add(raw_name)

    results.sort(key=lambda item: (score_theater_priority(item["code"]), item["name"]))
    return results


def build_card_location(theaters):
    names = [theater["name"] for theater in theaters]
    if not names:
        return "Selected Tokyo cinemas"
    if len(names) <= 3:
        return ", ".join(names)
    return f"{', '.join(names[:3])} + {len(names) - 3} more"


def extract_detail_fields(main_text: str):
    synopsis = normalize_space(main_text)
    director = ""
    cast = ""

    if "監督：" in synopsis:
        synopsis = synopsis.split("監督：", 1)[0].strip()

    director_match = re.search(r"監督：\s*(.+?)\s*出演：", main_text, flags=re.DOTALL)
    if director_match:
        director = normalize_space(director_match.group(1))

    cast_match = re.search(r"出演：\s*(.+?)(?:\s*公式サイト：|$)", main_text, flags=re.DOTALL)
    if cast_match:
        cast = normalize_space(cast_match.group(1))

    return synopsis, director, cast


def fetch_movie_detail(session, detail_url: str):
    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[109] Detail fetch failed: {detail_url} | {exc}")
        return {}

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")

    og_image = soup.find("meta", attrs={"property": "og:image"})
    title_tag = soup.find("title")
    main = soup.select_one(".main")
    hero_image = ""
    main_text = normalize_space(main.get_text(" ", strip=True)) if main else ""

    for image_tag in soup.find_all("img", src=True):
        candidate = image_tag.get("src", "").strip()
        if not candidate or "/media/" not in candidate:
            continue
        hero_image = urljoin(BASE_URL, candidate)
        break

    synopsis, director, cast = extract_detail_fields(main_text)
    raw_description = split_synopsis(synopsis)
    if director:
        raw_description.append(f"Director: {director}.")
    if cast:
        raw_description.append(f"Cast: {cast}.")

    title = ""
    if title_tag:
        title = normalize_space(title_tag.get_text(" ", strip=True))
        title = re.sub(r"\s*-\s*109.*$", "", title).strip()

    return {
        "title": title,
        "image": urljoin(BASE_URL, og_image.get("content", "")) if og_image else hero_image,
        "synopsis": synopsis,
        "director": director,
        "cast": cast,
        "raw_description": raw_description[:4],
    }


def fetch_109_now_showing_films(start_id=11101):
    session = create_session()

    try:
        response = session.get(NOW_SHOWING_URL, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[109] Now showing fetch failed: {exc}")
        return []

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    next_id = start_id

    for item in soup.select(".movies-list-movie"):
        values = [normalize_space(value) for value in item.stripped_strings if normalize_space(value)]
        if not values or "上映劇場" not in values:
            continue

        title = values[0]
        marker_index = values.index("上映劇場")
        theater_names = values[marker_index + 1 :]
        tokyo_theaters = pick_tokyo_theaters(theater_names)

        if not tokyo_theaters:
            continue

        link = item.find("a", href=True)
        if not link:
            continue

        detail_url = urljoin(BASE_URL, link["href"])
        detail = fetch_movie_detail(session, detail_url)
        image = detail.get("image", "")

        if not image:
            image_tag = item.find("img")
            if image_tag and image_tag.get("src"):
                image = urljoin(BASE_URL, image_tag["src"])

        raw_description = detail.get("raw_description") or [title]

        record = {
            "id": next_id,
            "slug": make_slug(f"109-{title}"),
            "title": detail.get("title") or title,
            "category": "Film",
            "location": build_card_location(tokyo_theaters),
            "venue": "Tokyo major cinemas",
            "date": "Now showing",
            "startDate": "",
            "endDate": "",
            "image": image,
            "access": ", ".join(theater["name"] for theater in tokyo_theaters),
            "price": "",
            "bookingUrl": detail_url,
            "source": "109 Cinemas",
            "sourceUrl": detail_url,
            "tags": ["film", "now showing", "109 cinemas", "tokyo cinemas"],
            "area": "Tokyo",
            "language": "ja",
            "director": detail.get("director", ""),
            "cast": detail.get("cast", ""),
            "screeningVenues": tokyo_theaters,
            "rawDescription": raw_description,
        }

        results.append(record)
        safe_title = record["title"].encode("ascii", errors="backslashreplace").decode("ascii")
        print(f"[109] Added film #{next_id}: {safe_title}")
        next_id += 1

    return results
