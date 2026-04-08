import html
import re

from bs4 import BeautifulSoup

from utils.http_utils import create_session


NOW_SHOWING_JSON_URL = "https://hlo.tohotheater.jp/data_net/json/movie/TNPI3090.JSON"
DETAIL_URL_TEMPLATE = "https://hlo.tohotheater.jp/net/movie/TNPI3060J01.do?sakuhin_cd={movie_code}"
THEATER_JSON_TEMPLATE = "https://hlo.tohotheater.jp/images_net/movie/{movie_code}/TNPI3060_2_{movie_code}.JSON"
IMAGE_URL_TEMPLATE = "https://hlo.tohotheater.jp/images_net/movie/{movie_code}/{file_name}"
TOKYO_PREFECTURE_NAME = "東京都"
IMPORTANT_TOKYO_THEATER_ORDER = [
    "日比谷",
    "シャンテ",
    "新宿",
    "六本木ヒルズ",
    "渋谷",
    "池袋",
    "日本橋",
    "上野",
    "錦糸町",
    "立川",
    "大井町",
    "府中",
    "南大沢",
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


def strip_html_text(value: str) -> str:
    if not value:
        return ""

    soup = BeautifulSoup(html.unescape(value), "html.parser")
    text = normalize_space(soup.get_text(" ", strip=True))
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text


def split_synopsis(text: str):
    cleaned = normalize_space(text)
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[。！？!?])\s*", cleaned)
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


def build_card_location(theaters):
    if not theaters:
        return "Selected Tokyo cinemas"

    if len(theaters) <= 3:
        return ", ".join(theaters)

    return f"{', '.join(theaters[:3])} + {len(theaters) - 3} more"


def extract_tokyo_theaters(payload):
    results = []

    for area in payload.get("data", [{}])[0].get("list", []):
        for prefecture in area.get("list", []):
            if prefecture.get("name") != TOKYO_PREFECTURE_NAME:
                continue

            for theater in prefecture.get("list", []):
                name = normalize_space(theater.get("name", ""))
                code = normalize_space(theater.get("code", ""))
                if not name or not code:
                    continue

                record = {
                    "name": name,
                    "code": code,
                    "url": f"https://www.tohotheater.jp/theater/{code}/access.html",
                }

                if record not in results:
                    results.append(record)

    return results


def score_theater_priority(name: str) -> int:
    for index, keyword in enumerate(IMPORTANT_TOKYO_THEATER_ORDER):
        if keyword in name:
            return index

    return len(IMPORTANT_TOKYO_THEATER_ORDER) + 1


def pick_important_tokyo_theaters(theaters, limit=5):
    if not theaters:
        return []

    sorted_theaters = sorted(
        theaters,
        key=lambda theater: (score_theater_priority(theater["name"]), theater["name"]),
    )

    return sorted_theaters[:limit]


def fetch_movie_detail(session, movie_code: str):
    detail_url = DETAIL_URL_TEMPLATE.format(movie_code=movie_code)

    try:
        response = session.get(detail_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[TOHO] Detail fetch failed for {movie_code}: {exc}")
        return {}

    response.encoding = "shift_jis"
    soup = BeautifulSoup(response.text, "html.parser")

    og_image = soup.find("meta", attrs={"property": "og:image"})
    og_description = soup.find("meta", attrs={"property": "og:description"})
    title_tag = soup.find("title")

    image = normalize_space(og_image.get("content", "")) if og_image else ""
    synopsis = strip_html_text(og_description.get("content", "")) if og_description else ""
    title = ""

    if title_tag:
        title = normalize_space(title_tag.get_text(" ", strip=True))
        title = re.sub(r"\s*\|\|.*$", "", title).strip()

    return {
        "detail_url": detail_url,
        "title": title,
        "image": image.replace("http://", "https://"),
        "synopsis": synopsis,
        "raw_description": split_synopsis(synopsis),
    }


def fetch_tokyo_theater_payload(session, movie_code: str):
    theater_url = THEATER_JSON_TEMPLATE.format(movie_code=movie_code)

    try:
        response = session.get(theater_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"[TOHO] Theater fetch failed for {movie_code}: {exc}")
        return {}


def fetch_toho_now_showing_films(start_id=11001):
    session = create_session()

    try:
        response = session.get(NOW_SHOWING_JSON_URL, timeout=30)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print(f"[TOHO] Now playing fetch failed: {exc}")
        return []

    results = []
    next_id = start_id

    for item in payload.get("data", []):
        movie_code = normalize_space(item.get("mcode", ""))
        title = normalize_space(item.get("name", ""))

        if not movie_code or not title:
            continue

        theater_payload = fetch_tokyo_theater_payload(session, movie_code)
        tokyo_theaters = extract_tokyo_theaters(theater_payload)

        if not tokyo_theaters:
            continue

        important_tokyo_theaters = pick_important_tokyo_theaters(tokyo_theaters)
        important_theater_names = [theater["name"] for theater in important_tokyo_theaters]

        detail = fetch_movie_detail(session, movie_code)
        image_name = normalize_space(item.get("sakuhinGazouNm", ""))
        fallback_image = ""
        if image_name:
            fallback_image = IMAGE_URL_TEMPLATE.format(movie_code=movie_code, file_name=image_name)

        synopsis = detail.get("synopsis") or ""
        director = normalize_space(item.get("kantokuNm", ""))
        cast = normalize_space(item.get("syutuenSyaNm", ""))

        raw_description = detail.get("raw_description") or []
        if director:
            raw_description.append(f"Director: {director}.")
        if cast:
            raw_description.append(f"Cast: {cast}.")

        if not raw_description:
            raw_description = [title]

        record = {
            "id": next_id,
            "slug": make_slug(f"toho-{title}-{movie_code}"),
            "title": detail.get("title") or title,
            "category": "Film",
            "location": build_card_location(important_theater_names),
            "venue": "TOHO Cinemas Tokyo",
            "date": "Now showing",
            "startDate": "",
            "endDate": "",
            "image": detail.get("image") or fallback_image,
            "access": ", ".join(important_theater_names),
            "price": "",
            "bookingUrl": detail.get("detail_url") or DETAIL_URL_TEMPLATE.format(movie_code=movie_code),
            "source": "TOHO Cinemas",
            "sourceUrl": detail.get("detail_url") or DETAIL_URL_TEMPLATE.format(movie_code=movie_code),
            "tags": ["film", "now showing", "tokyo cinemas"],
            "area": "Tokyo",
            "language": "ja",
            "director": director,
            "cast": cast,
            "screeningVenues": important_tokyo_theaters,
            "rawDescription": raw_description[:4],
        }

        results.append(record)
        safe_title = record["title"].encode("ascii", errors="backslashreplace").decode("ascii")
        print(f"[TOHO] Added film #{next_id}: {safe_title}")
        next_id += 1

    return results
