import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score


# =========================
# Tokyo Metropolitan Art Museum
# =========================

def fetch_tobikan_exhibitions(start_id=8001):
    """Scrape current and upcoming exhibitions from Tokyo Metropolitan Art Museum."""
    base_url = "https://www.tobikan.jp/en/exhibition/index.html"
    print(f"[TOBIKAN] Fetching {base_url}")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        response = session.get(base_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[TOBIKAN] Error fetching page: {exc}")
        return []

    response.encoding = response.apparent_encoding or response.encoding
    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    next_id = start_id
    seen_titles = set()
    detail_page_cache = {}

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

    def clean_tobikan_title(title: str) -> str:
        title = normalize_space(title)
        prefix = "100th Anniversary of the Tokyo Metropolitan Art Museum "
        if title.startswith(prefix):
            title = title[len(prefix):].strip()
        return title

    def fetch_detail_page(detail_url):
        if not detail_url:
            return None

        if detail_url in detail_page_cache:
            return detail_page_cache[detail_url]

        try:
            resp = session.get(detail_url, timeout=20)
            resp.raise_for_status()
            detail_soup = BeautifulSoup(resp.text, "html.parser")
            detail_page_cache[detail_url] = detail_soup
            return detail_soup
        except Exception as exc:
            print(f"[TOBIKAN] Detail page fetch failed: {detail_url} | {exc}")
            detail_page_cache[detail_url] = None
            return None

    def fetch_detail_description(detail_url: str, fallback_text: str = ""):
        """
        进入详情页抓正文段落，返回 rawDescription 列表。
        如果抓不到正文，则退回到 period/title 的简化信息。
        """
        detail_soup = fetch_detail_page(detail_url)
        texts = []
        seen_texts = set()

        if detail_soup is not None:
            selectors = [
                ".boxArticle p",
                ".articleBody p",
                ".entry-content p",
                ".post-content p",
                ".contents p",
                "main p",
                "article p",
            ]

            for selector in selectors:
                paragraphs = detail_soup.select(selector)
                if not paragraphs:
                    continue

                for p in paragraphs:
                    text = normalize_space(p.get_text(" ", strip=True))
                    lower = text.lower()

                    if not text:
                        continue
                    if len(text) < 40:
                        continue

                    if any(bad in lower for bad in [
                        "admission",
                        "closed",
                        "opening hours",
                        "access",
                        "contact",
                        "facebook",
                        "instagram",
                        "twitter",
                        "x.com",
                        "copyright",
                        "venue",
                    ]):
                        continue

                    if text in seen_texts:
                        continue

                    seen_texts.add(text)
                    texts.append(text)

                if len(texts) >= 2:
                    break

        if not texts and fallback_text:
            texts = [fallback_text]

        if texts:
            print(f"[TOBIKAN] Detail description found: {len(texts)} paragraphs")
        else:
            print(f"[TOBIKAN] No detail description found: {detail_url}")

        return texts[:6]

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

        source_url = make_absolute(href) if href else base_url
        fallback_text = f"{title}. {date_text}" if date_text else title
        raw_description = fetch_detail_description(source_url, fallback_text=fallback_text)

        record = {
            "id": next_id,
            "slug": make_slug(title),
            "title": title,
            "category": "Exhibition",
            "location": "Tokyo Metropolitan Art Museum (Ueno)",
            "venue": "Tokyo Metropolitan Art Museum",
            "date": date_text or "See source",
            "startDate": "",
            "endDate": "",
            "image": make_absolute(img_src) if img_src else "",
            "access": "Ueno Station",
            "price": "",
            "bookingUrl": "",
            "source": "Tokyo Metropolitan Art Museum",
            "sourceUrl": source_url,
            "tags": [],
            "area": "Ueno",
            "language": "en",
            "rawDescription": raw_description,
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
            img_src = ""
            if img_tag:
                img_src = img_tag.get("src") or img_tag.get("data-src") or ""

            if not title:
                print("[TOBIKAN] Skipping card without title")
                continue

            append_item(title, date_text, href, img_src)

    print(f"[TOBIKAN] Total exhibitions collected: {len(results)}")
    return results