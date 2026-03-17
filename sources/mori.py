import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score
import re

# =========================
# 展览来源 Mori Art Museum
# =========================

def fetch_mori_exhibitions(start_id=7001):
    """
    从 Mori Art Museum 英文展览页抓取当前和即将开始的展览。
    """
    base_url = "https://www.mori.art.museum/en/exhibitions/"
    print(f"[MORI] Fetching {base_url}")

    try:
        response = requests.get(
            base_url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        response.raise_for_status()
    except Exception as exc:
        print(f"[MORI] Error fetching page: {exc}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results = []
    seen = set()
    next_id = start_id

    def normalize_space(text):
        return " ".join((text or "").split())

    def make_absolute(path: str) -> str:
        return urljoin(base_url, path) if path else ""

    def split_title_and_date(text: str):
        text = normalize_space(text)
        if not text:
            return "", ""

        m = re.search(r"\d{4}\.\d{1,2}\.\d{1,2}\s*\[[A-Za-z]{3}\]", text)
        if m:
            return text[:m.start()].strip(), text[m.start():].strip()

        return text, ""

    def clean_mori_title(title: str):
        title = normalize_space(title)

        replacements = [
            ("MAM Collection MAM Collection", "MAM Collection"),
            ("MAM Screen MAM Screen", "MAM Screen"),
            ("MAM Project MAM Project", "MAM Project"),
        ]

        for old, new in replacements:
            title = title.replace(old, new)

        return title

    def detect_section(anchor):
        for elem in anchor.previous_elements:
            if not getattr(elem, "name", None):
                continue

            if elem.name.lower() not in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "span"):
                continue

            txt = normalize_space(elem.get_text(" ", strip=True)).lower()
            if not txt:
                continue

            if "more pick-ups" in txt:
                return "more_pickups"
            if "upcoming exhibitions" in txt:
                return "upcoming"
            if "also on view" in txt:
                return "also_on_view"
            if "current exhibitions" in txt:
                return "current"

        return "unknown"

    def find_image_url(anchor):
        candidates = []

        img = anchor.find("img")
        if img:
            candidates.append(img)

        parent = anchor.parent
        if parent:
            img = parent.find("img")
            if img:
                candidates.append(img)

        grand = parent.parent if parent else None
        if grand:
            img = grand.find("img")
            if img:
                candidates.append(img)

        for tag in candidates:
            src = (
                tag.get("data-pcimg")
                or tag.get("data-spimg")
                or tag.get("data-src")
                or tag.get("src")
                or ""
            )
            if src:
                return make_absolute(src)

        return ""

    def append_item(title, date_text, href, img_src, section):
        nonlocal next_id

        if not title:
            return

        key = normalize_text(title)
        if key in seen:
            print(f"[MORI] Skipping duplicate: {title}")
            return
        seen.add(key)

        section_label_map = {
            "current": "Current Exhibition",
            "also_on_view": "Also on View",
            "upcoming": "Upcoming Exhibition",
        }

        record = {
            "id": next_id,
            "title": title,
            "category": "Exhibition",
            "location": "Mori Art Museum (Roppongi Hills)",
            "venue": "Mori Art Museum",
            "date": date_text or "See source",
            "image": img_src or "https://picsum.photos/seed/mori-exhibition/400/200",
            "description": f"{section_label_map.get(section, 'Exhibition')} at Mori Art Museum",
            "source": "Mori Art Museum",
            "sourceUrl": make_absolute(href) if href else base_url,
            "sources": ["Mori Art Museum"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "moriSection": section,
            "score": 0,
        }

        record["score"] = calculate_exhibition_score(record)

        results.append(record)
        print(f"[MORI] Added exhibition #{next_id}: {title} ({section})")
        next_id += 1

    links = soup.select("a")
    print(f"[MORI] Raw anchor tags found: {len(links)}")

    exclude_keywords = [
        "buy tickets",
        "become a member",
        "museum & observatory",
        "past exhibitions",
        "exhibition tours and others",
        "more pick-ups",
        "tokyo city view",
        "mori arts center gallery",
        "online shop",
        "museum shop",
        "visit us",
        "access",
        "services",
        "specials",
        "faq",
        "inquiries",
        "current / upcoming exhibitions",
        "current exhibitions",
        "upcoming exhibitions",
    ]

    allowed_sections = {"current", "also_on_view", "upcoming"}

    for a in links:
        href = a.get("href", "") or ""
        text = normalize_space(a.get_text(" ", strip=True))

        if not text:
            continue

        lower_text = text.lower()

        if len(text) < 6:
            continue

        if lower_text in {
            "current / upcoming exhibitions",
            "current exhibitions",
            "upcoming exhibitions",
            "also on view",
            "more pick-ups",
        }:
            continue

        if any(word in lower_text for word in exclude_keywords):
            continue

        section = detect_section(a)
        if section not in allowed_sections:
            continue

        title, date_text = split_title_and_date(text)
        title = clean_mori_title(title)

        if not title:
            continue

        img_src = find_image_url(a)

        append_item(
            title=title,
            date_text=date_text,
            href=href,
            img_src=img_src,
            section=section,
        )

    section_order = {
        "current": 0,
        "also_on_view": 1,
        "upcoming": 2,
    }
    results.sort(key=lambda x: (section_order.get(x.get("moriSection", ""), 99), x["id"]))

    print(f"[MORI] Total exhibitions collected: {len(results)}")
    return results