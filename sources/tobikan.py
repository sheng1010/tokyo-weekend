import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score

# =========================
# Tokyo Metropolitan Art Museum
# =========================

def fetch_tobikan_exhibitions(start_id=8001):
    """Scrape current and upcoming exhibitions from Tokyo Metropolitan Art Museum."""
    base_url = "https://www.tobikan.jp/en/exhibition/index.html"
    print(f"[TOBIKAN] Fetching {base_url}")

    try:
        response = requests.get(
            base_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        response.raise_for_status()
    except Exception as exc:
        print(f"[TOBIKAN] Error fetching page: {exc}")
        return []

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    next_id = start_id
    seen_titles = set()

    def make_absolute(path: str) -> str:
        return urljoin(base_url, path) if path else ""

    def clean_tobikan_title(title: str) -> str:
        title = " ".join((title or "").split())
        prefix = "100th Anniversary of the Tokyo Metropolitan Art Museum "
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
        return title

    bad_titles = {
        "past exhibitions",
        "exhibition calendar",
        "exhibition archive",
    }

    def append_item(title, date_text, href, img_src):
        nonlocal next_id

        title = clean_tobikan_title(title)
        key = normalize_text(title)

        if key in bad_titles:
            print(f"[TOBIKAN] Skipping non-exhibition title: {title}")
            return

        if key in seen_titles:
            print(f"[TOBIKAN] Skipping duplicate title: {title}")
            return
        seen_titles.add(key)

        record = {
            "id": next_id,
            "title": title,
            "category": "Exhibition",
            "location": "Tokyo Metropolitan Art Museum (Ueno)",
            "venue": "Tokyo Metropolitan Art Museum",
            "date": date_text or "See source",
            "image": make_absolute(img_src) if img_src else "https://picsum.photos/seed/tobikan-exhibition/400/200",
            "description": f"{title} at Tokyo Metropolitan Art Museum",
            "source": "Tokyo Metropolitan Art Museum",
            "sourceUrl": make_absolute(href) if href else base_url,
            "sources": ["Tokyo Metropolitan Art Museum"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "score": 0,
        }
        record["score"] = calculate_exhibition_score(record)

        results.append(record)
        print(f"[TOBIKAN] Added exhibition #{next_id}: {title}")
        next_id += 1

    header_order = ["anchor1", "anchor2"]

    for header_id in header_order:
        header = soup.find("div", id=header_id)
        if not header:
            print(f"[TOBIKAN] Section with id '{header_id}' not found")
            continue

        header_title_tag = header.find("h3", class_="section-header-title")
        header_label = header_title_tag.get_text(strip=True) if header_title_tag else header_id

        ul = header.find_next_sibling()
        while ul and ul.name != "ul":
            ul = ul.find_next_sibling()

        if not ul or "exhibition-list" not in (ul.get("class") or []):
            print(f"[TOBIKAN] No exhibition list found for section '{header_label}'")
            continue

        cards = ul.select("a.exhibition-item")
        print(f"[TOBIKAN] Section '{header_label}' has {len(cards)} cards")

        for card in cards:
            title_tag = card.select_one("p.-title")
            period_tag = card.select_one("p.-period")
            img_tag = card.select_one("p.-image img")

            title = title_tag.get_text(" ", strip=True) if title_tag else ""
            date_text = period_tag.get_text(" ", strip=True) if period_tag else ""
            href = card.get("href", "")
            img_src = img_tag.get("src") or img_tag.get("data-src") or "" if img_tag else ""

            if not title:
                print("[TOBIKAN] Skipping card without title")
                continue

            append_item(title, date_text, href, img_src)

    print(f"[TOBIKAN] Total exhibitions collected: {len(results)}")
    return results