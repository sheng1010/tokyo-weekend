import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score
from utils.common_utils import normalize_text
import re

# =========================
# Tokyo National Museum
# =========================

def fetch_tnm_exhibitions(start_id=10001):
    """Scrape current exhibitions from Tokyo National Museum."""
    base_url = "https://www.tnm.jp/?lang=en"
    fallback_image = "https://picsum.photos/seed/tnm-exhibition/400/200"

    print(f"[TNM] Fetching {base_url}")
    try:
        response = requests.get(
            base_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
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
        return normalize_space(BeautifulSoup(raw, "html.parser").get_text(" "))

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

        record = {
            "id": start_id,
            "title": title_clean,
            "category": "Exhibition",
            "location": "Tokyo National Museum (Ueno)",
            "venue": "Tokyo National Museum",
            "date": final_date,
            "image": image or fallback_image,
            "description": f"{title_clean} at Tokyo National Museum",
            "source": "Tokyo National Museum",
            "sourceUrl": url,
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