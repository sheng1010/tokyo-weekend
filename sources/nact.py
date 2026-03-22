import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score


def parse_nact_special_exhibitions(soup, append_item, normalize_space):
    """
    解析 NACT 页面中的 Special exhibitions。
    """
    special_items = soup.select("ul.main_box > li")
    print(f"[NACT] Found {len(special_items)} special exhibition cards")

    for block in special_items:
        anchor = block.find("a", href=True)
        title_tag = block.find("h2")
        date_tag = block.select_one("p.ex_date")
        img_tag = block.select_one("p.img_area img")

        categories = [
            normalize_space(c.get_text(" ", strip=True))
            for c in block.select(".ex_cate li")
        ]
        categories = [c for c in categories if c]
        meta_description = " / ".join(categories)

        append_item(
            title=title_tag.get_text(" ", strip=True) if title_tag else "",
            date_text=date_tag.get_text(" ", strip=True) if date_tag else "",
            href=anchor.get("href", "") if anchor else "",
            img_src=img_tag.get("src", "") if img_tag else "",
            meta_description=meta_description,
        )


def parse_nact_public_exhibitions(soup, append_item, normalize_space):
    """
    解析 NACT 页面中的 Artist associations' exhibitions。
    """
    public_items = soup.select("ul.public_box > li")
    print(f"[NACT] Found {len(public_items)} artist association entries")

    for block in public_items:
        anchor = block.find("a", href=True)
        href = anchor.get("href", "") if anchor else ""
        title_tag = block.find("h2")
        date_tag = block.select_one("p.ex_date")
        img_tag = block.select_one("p.public_img img")

        detail_parts = []

        target_id = ""
        if href.startswith("#"):
            target_id = href[1:]
        elif "#" in href:
            target_id = href.split("#", 1)[1]

        if target_id:
            detail_block = soup.find(id=target_id)
            if detail_block:
                for row in detail_block.select("dl.dl2 > div"):
                    dt = row.find("dt")
                    dd = row.find("dd")

                    label = normalize_space(dt.get_text(" ", strip=True)) if dt else ""
                    value = normalize_space(" ".join(dd.stripped_strings)) if dd else ""

                    if label and value:
                        detail_parts.append(f"{label}: {value}")

        if not detail_parts:
            categories = [
                normalize_space(c.get_text(" ", strip=True))
                for c in block.select(".ex_cate li")
            ]
            categories = [c for c in categories if c]
            if categories:
                detail_parts.append(" / ".join(categories))

        append_item(
            title=title_tag.get_text(" ", strip=True) if title_tag else "",
            date_text=date_tag.get_text(" ", strip=True) if date_tag else "",
            href=href,
            img_src=img_tag.get("src", "") if img_tag else "",
            meta_description=" | ".join(detail_parts),
        )


# =========================
# 展览来源 The National Art Center, Tokyo（NACT）
# =========================
def fetch_nact_exhibitions(start_id=6001):
    """Scrape current and upcoming exhibitions from The National Art Center, Tokyo."""
    base_url = "https://www.nact.jp/english/exhibition_and_event/"
    fallback_image = ""

    print(f"[NACT] Fetching {base_url}")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        resp = session.get(base_url, timeout=30)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[NACT] Error fetching page: {exc}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    next_id = start_id
    seen_keys = set()
    detail_page_cache = {}

    def normalize_space(text):
        return " ".join((text or "").split())

    def make_absolute(path: str) -> str:
        return urljoin(base_url, path) if path else ""

    def build_source_url(href: str) -> str:
        href = (href or "").strip()
        if not href:
            return base_url
        return urljoin(base_url, href)

    def make_slug(text: str):
        text = (text or "").lower().strip()
        text = text.replace("&", " and ")
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"\s+", "-", text)
        text = re.sub(r"-+", "-", text)
        return text.strip("-")

    def clean_title(title: str) -> str:
        return normalize_space(title)

    def clean_date(date_text: str) -> str:
        return normalize_space(date_text)

    def clean_description(description: str) -> str:
        return normalize_space(description)

    def should_skip(title: str) -> bool:
        t = normalize_text(title)
        if not t:
            return True

        bad_exact = {
            "exhibition and event",
            "exhibitions and events",
        }
        if t in bad_exact:
            return True

        return False

    def fetch_detail_page(detail_url):
        if not detail_url:
            return None

        if detail_url in detail_page_cache:
            return detail_page_cache[detail_url]

        try:
            resp = session.get(detail_url, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            detail_page_cache[detail_url] = soup
            return soup
        except Exception as exc:
            print(f"[NACT] Detail page fetch failed: {detail_url} | {exc}")
            detail_page_cache[detail_url] = None
            return None

    def fetch_detail_description(detail_url: str, fallback_meta: str = ""):
        """
        进入详情页抓正文段落，返回 rawDescription 列表。
        如果抓不到正文，就退回到列表页已有的 meta_description。
        """
        soup = fetch_detail_page(detail_url)
        texts = []
        seen_texts = set()

        if soup is not None:
            selectors = [
                ".content_box p",
                ".entry-content p",
                ".post-content p",
                ".contents p",
                ".main_box p",
                "main p",
                "article p",
            ]

            for selector in selectors:
                paragraphs = soup.select(selector)
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

        if not texts and fallback_meta:
            texts = [fallback_meta]

        if texts:
            print(f"[NACT] Detail description found: {len(texts)} paragraphs")
        else:
            print(f"[NACT] No detail description found: {detail_url}")

        return texts[:6]

    def append_item(title, date_text, href, img_src, meta_description):
        nonlocal next_id

        title = clean_title(title)
        date_text = clean_date(date_text)
        meta_description = clean_description(meta_description)

        if should_skip(title):
            print(f"[NACT] Skipping non-exhibition title: {title}")
            return

        source_url = build_source_url(href)
        image_url = make_absolute(img_src) if img_src else fallback_image
        raw_description = fetch_detail_description(source_url, fallback_meta=meta_description)

        key = (
            normalize_text(title),
            normalize_text("The National Art Center, Tokyo"),
            normalize_text(date_text),
        )

        if key in seen_keys:
            print(f"[NACT] Skipping duplicate: {title}")
            return
        seen_keys.add(key)

        record = {
            "id": next_id,
            "slug": make_slug(title),
            "title": title,
            "category": "Exhibition",
            "location": "The National Art Center, Tokyo (Roppongi)",
            "venue": "The National Art Center, Tokyo",
            "date": date_text or "See source",
            "startDate": "",
            "endDate": "",
            "image": image_url,
            "access": "Nogizaka Station (Chiyoda Line), direct connection / Roppongi Station within walking distance",
            "price": "",
            "bookingUrl": "",
            "source": "The National Art Center, Tokyo",
            "sourceUrl": source_url,
            "tags": [],
            "area": "Roppongi",
            "language": "en",
            "rawDescription": raw_description,
            "sources": ["The National Art Center, Tokyo"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "score": 0,
        }
        record["score"] = calculate_exhibition_score(record)

        results.append(record)
        print(f"[NACT] Added exhibition #{next_id}: {title}")
        next_id += 1

    parse_nact_special_exhibitions(
        soup=soup,
        append_item=append_item,
        normalize_space=normalize_space,
    )

    parse_nact_public_exhibitions(
        soup=soup,
        append_item=append_item,
        normalize_space=normalize_space,
    )

    print(f"[NACT] Total exhibitions collected: {len(results)}")
    return results