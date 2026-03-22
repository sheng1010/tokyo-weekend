import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score


# =========================
# Tokyo National Museum
# =========================

def fetch_tnm_exhibitions(start_id=10001):
    """Scrape current exhibitions from Tokyo National Museum."""
    base_url = "https://www.tnm.jp/?lang=en"
    fallback_image = ""

    print(f"[TNM] Fetching {base_url}")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        response = session.get(base_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"[TNM] Error fetching page: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    def normalize_space(text):
        return " ".join((text or "").split())

    def make_absolute(url):
        return urljoin(base_url, url) if url else ""

    def clean_title(raw):
        if not raw:
            return ""
        return normalize_space(BeautifulSoup(str(raw), "html.parser").get_text(" "))

    def make_slug(text: str):
        text = (text or "").lower().strip()
        text = text.replace("&", " and ")
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"\s+", "-", text)
        text = re.sub(r"-+", "-", text)
        return text.strip("-")

    date_pattern = re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}(?:\s*[–-]\s*(January|February|March|April|May|June|July|August|September|October|November|December)?"
        r"\s*\d{1,2})?(?:,?\s*\d{4})?",
        re.IGNORECASE,
    )

    def split_title_date(text):
        text = normalize_space(text)
        if not text:
            return "", ""

        date_text = ""
        match = date_pattern.search(text)
        if match:
            date_text = normalize_space(match.group().strip(" -–|,:"))
            text = (text[:match.start()] + text[match.end():]).strip(" -–|,:")
        return text, date_text

    exclude_exact = {
        "jump to content",
        "français",
        "this week's change of exhibits",
        "this week’s change of exhibits",
        "schedule",
        "special exhibitions",
        "past special exhibitions",
        "exhibitions",
        "guide",
        "access",
        "calendar",
        "faq",
        "inquiries",
        "museum shop",
        "online shop",
        "visit us",
    }

    exclude_contains = [
        "language",
        "ticket",
        "menu",
        "shop",
        "guide",
        "faq",
        "inquir",
        "access",
        "calendar",
    ]

    def should_skip(title):
        normalized = normalize_text(title)
        if not normalized or len(normalized) < 4:
            return True
        if normalized in exclude_exact:
            return True
        for phrase in exclude_contains:
            if phrase in normalized:
                return True
        return False

    detail_page_cache = {}

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
            print(f"[TNM] Detail page fetch failed: {detail_url} | {exc}")
            detail_page_cache[detail_url] = None
            return None

    def fetch_detail_description(detail_url: str):
        """
        进入详情页抓正文段落，返回 rawDescription 列表。
        """
        detail_soup = fetch_detail_page(detail_url)
        if detail_soup is None:
            return []

        selectors = [
            ".section p",
            ".article p",
            ".content p",
            ".contents p",
            ".post p",
            "main p",
            "article p",
        ]

        texts = []
        seen_texts = set()

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
                    "ticket",
                    "admission",
                    "access",
                    "hours",
                    "closed",
                    "inquiry",
                    "contact",
                    "facebook",
                    "instagram",
                    "twitter",
                    "x.com",
                    "copyright",
                ]):
                    continue

                if text in seen_texts:
                    continue

                seen_texts.add(text)
                texts.append(text)

            if len(texts) >= 2:
                break

        if texts:
            print(f"[TNM] Detail description found: {len(texts)} paragraphs")
        else:
            print(f"[TNM] No detail description found: {detail_url}")

        return texts[:6]

    results = []
    seen_titles = set()
    seen_urls = set()

    def add_entry(title, date_text, url, image):
        nonlocal start_id

        if not url:
            print(f"[TNM] Skipping entry without URL: {title}")
            return

        title_clean, title_date = split_title_date(title)
        title_clean = clean_title(title_clean)

        if should_skip(title_clean):
            print(f"[TNM] Skipping non-exhibition title: {title_clean}")
            return

        key = normalize_text(title_clean)
        if key in seen_titles or url in seen_urls:
            print(f"[TNM] Skipping duplicate: {title_clean}")
            return

        final_date = normalize_space(date_text) or title_date or "See source"
        raw_description = fetch_detail_description(url)

        if not raw_description:
            raw_description = [
                f"{title_clean}. {final_date}"
            ]

        record = {
            "id": start_id,
            "slug": make_slug(title_clean),
            "title": title_clean,
            "category": "Exhibition",
            "location": "Tokyo National Museum (Ueno)",
            "venue": "Tokyo National Museum",
            "date": final_date,
            "startDate": "",
            "endDate": "",
            "image": image or fallback_image,
            "access": "Ueno Station",
            "price": "",
            "bookingUrl": "",
            "source": "Tokyo National Museum",
            "sourceUrl": url,
            "tags": [],
            "area": "Ueno",
            "language": "en",
            "rawDescription": raw_description,
            "sources": ["Tokyo National Museum"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "score": 0,
        }
        record["score"] = calculate_exhibition_score(record)

        results.append(record)
        seen_titles.add(key)
        seen_urls.add(url)
        print(f"[TNM] Added exhibition #{start_id}: {title_clean}")
        start_id += 1

    hero_blocks = soup.select(".top-attention-exhibition__main .exhibition_wrapper")
    print(f"[TNM] Hero blocks found: {len(hero_blocks)}")
    for wrapper in hero_blocks:
        desc = wrapper.select_one(".exhibition_item._desc")
        if not desc:
            continue

        title_el = desc.select_one(".title .desc") or desc.select_one(".title")
        link_el = desc.select_one(".wrap_btn a")
        date_el = desc.select_one(".date")
        img_el = wrapper.select_one(".exhibition_item._img img")

        title = clean_title(title_el.get_text(" ", strip=True)) if title_el else ""
        date_text = normalize_space(date_el.get_text(" ", strip=True)) if date_el else ""
        url = make_absolute(link_el.get("href", "")) if link_el else ""
        image = make_absolute(img_el.get("src", "")) if img_el else ""

        add_entry(title, date_text, url, image)

    card_nodes = soup.select(".top-exihibiton-list li")
    print(f"[TNM] Exhibition cards found: {len(card_nodes)}")
    for card in card_nodes:
        link_el = card.find("a", href=True)
        title_el = card.select_one(".text .desc")
        date_el = card.select_one(".text .date")
        img_el = card.select_one(".img img")

        title = clean_title(title_el.get_text(" ", strip=True)) if title_el else ""
        date_text = normalize_space(date_el.get_text(" ", strip=True)) if date_el else ""
        url = make_absolute(link_el.get("href", "")) if link_el else ""
        image = make_absolute(img_el.get("src", "")) if img_el else ""

        add_entry(title, date_text, url, image)

    print(f"[TNM] Total exhibitions collected: {len(results)}")
    return results