import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score


# =========================
# 展览来源 Mori Art Museum
# =========================

def fetch_mori_exhibitions(start_id=7001):
    """
    从 Mori Art Museum 英文展览页抓取当前和即将开始的展览。
    同时进入详情页抓取 rawDescription，供 build_events.py 使用。
    """
    base_url = "https://www.mori.art.museum/en/exhibitions/"
    print(f"[MORI] Fetching {base_url}")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        response = session.get(base_url, timeout=30)
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

    def fetch_detail_description(detail_url: str):
        """
        进入 Mori 展览详情页抓取正文段落，返回 rawDescription 列表。
        """
        if not detail_url:
            return []

        try:
            resp = session.get(detail_url, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            print(f"[MORI] Detail fetch failed: {detail_url} | {exc}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        candidates = [
            ".exhibition-body p",
            ".contents p",
            ".content p",
            "main p",
            "article p",
        ]

        texts = []
        seen_texts = set()

        for selector in candidates:
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

                # 过滤明显无用内容
                if any(bad in lower for bad in [
                    "share",
                    "facebook",
                    "twitter",
                    "instagram",
                    "related programs",
                    "ticket",
                    "admission",
                    "hours",
                    "closed",
                    "contact",
                    "access",
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
            print(f"[MORI] Detail description found: {len(texts)} paragraphs")
        else:
            print(f"[MORI] No detail description found: {detail_url}")

        return texts[:6]

    def append_item(title, date_text, href, img_src, section):
        nonlocal next_id

        if not title:
            return

        key = normalize_text(title)
        if key in seen:
            print(f"[MORI] Skipping duplicate: {title}")
            return
        seen.add(key)

        detail_url = make_absolute(href)
        raw_description = fetch_detail_description(detail_url)

        record = {
            "id": next_id,
            "slug": re.sub(r"-+", "-", re.sub(r"[^\w\s-]", "", title.lower()).replace("&", " and ").strip().replace(" ", "-")).strip("-"),
            "title": title,
            "category": "Exhibition",
            "location": "Mori Art Museum (Roppongi Hills)",
            "venue": "Mori Art Museum",
            "date": date_text or "See source",
            "startDate": "",
            "endDate": "",
            "image": img_src or "",
            "access": "Roppongi Station (Hibiya Line / Oedo Line), direct access to Roppongi Hills",
            "price": "",
            "bookingUrl": "",
            "source": "Mori Art Museum",
            "sourceUrl": detail_url if detail_url else base_url,
            "tags": [],
            "area": "Roppongi",
            "language": "en",
            "rawDescription": raw_description,
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