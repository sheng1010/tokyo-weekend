import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone, timedelta
import re

from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score


# =========================
# 展览来源 Museum of Contemporary Art Tokyo
# =========================
def fetch_mot_exhibitions(start_id=9001):
    """Scrape current and upcoming exhibitions from Museum of Contemporary Art Tokyo."""
    base_url = "https://www.mot-art-museum.jp/en/exhibitions/"
    json_url = "https://www.mot-art-museum.jp/en/json/exhibitions/exhibitions.json"
    fallback_image = ""

    print(f"[MOT] Fetching {base_url}")

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    try:
        html_resp = session.get(base_url, timeout=30)
        html_resp.raise_for_status()
    except Exception as exc:
        print(f"[MOT] Error fetching page: {exc}")
        return []

    try:
        data_resp = session.get(json_url, timeout=30)
        data_resp.raise_for_status()
        items = data_resp.json()
    except Exception as exc:
        print(f"[MOT] Error fetching JSON: {exc}")
        return []

    if isinstance(items, dict):
        if "items" in items:
            items = items["items"]
        elif "data" in items:
            items = items["data"]
        else:
            print(f"[MOT] Unexpected JSON structure: {list(items.keys())}")
            return []

    if not isinstance(items, list):
        print(f"[MOT] Unexpected JSON type: {type(items)}")
        return []

    tz = timezone(timedelta(hours=9))
    today = datetime.now(tz).date()

    exhibitions = []
    seen_titles = set()
    detail_page_cache = {}

    def clean_title(raw):
        if not raw:
            return ""
        text = BeautifulSoup(str(raw), "html.parser").get_text(" ")
        return " ".join(text.split())

    def make_slug(text: str):
        text = (text or "").lower().strip()
        text = text.replace("&", " and ")
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"\s+", "-", text)
        text = re.sub(r"-+", "-", text)
        return text.strip("-")

    def to_date(value):
        if value is None:
            return None

        value = str(value).strip()
        if not value:
            return None

        for fmt in ("%Y%m%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass

        return None

    def format_date(dt):
        return dt.strftime("%Y.%m.%d [%a]")

    def build_date_text(item, start_date, end_date):
        label = item.get("anotherDate")
        if label:
            return " ".join(str(label).split())

        if start_date and end_date:
            if start_date == end_date:
                return format_date(start_date)
            return f"{format_date(start_date)} - {format_date(end_date)}"

        if start_date:
            return format_date(start_date)

        return ""

    def make_absolute(url):
        return urljoin(base_url, url) if url else ""

    def is_valid_image(url):
        if not url:
            return False

        low = url.lower()

        invalid_keywords = [
            "no_image",
            "og-image",
            "/_assets/images/head/",
            "logo",
        ]

        return not any(k in low for k in invalid_keywords)

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
            print(f"[MOT] Detail page fetch failed: {detail_url} | {exc}")
            detail_page_cache[detail_url] = None
            return None

    def fetch_detail_page_image(detail_url):
        """
        进入详情页抓真正的展览图片：
        1. 优先正文区域图片
        2. 最后再尝试 og:image / twitter:image
        3. 自动排除站点通用 logo / og-image
        """
        soup = fetch_detail_page(detail_url)
        if soup is None:
            return ""

        candidates = []

        content_selectors = [
            "main img",
            ".l-main img",
            ".p-single img",
            ".entry-content img",
            ".post-content img",
            ".contents img",
            "article img",
        ]

        for selector in content_selectors:
            for img in soup.select(selector):
                src = (
                    img.get("src")
                    or img.get("data-src")
                    or img.get("data-original")
                    or ""
                ).strip()
                if src:
                    candidates.append(src)

        og = soup.select_one('meta[property="og:image"]')
        if og and og.get("content"):
            candidates.append(og.get("content").strip())

        tw = soup.select_one('meta[name="twitter:image"]')
        if tw and tw.get("content"):
            candidates.append(tw.get("content").strip())

        seen = set()
        for cand in candidates:
            abs_url = urljoin(detail_url, cand)
            if abs_url in seen:
                continue
            seen.add(abs_url)

            if is_valid_image(abs_url):
                return abs_url

        return ""

    def fetch_detail_description(detail_url):
        """
        进入详情页抓正文段落，返回 rawDescription 列表。
        """
        soup = fetch_detail_page(detail_url)
        if soup is None:
            return []

        selectors = [
            ".l-main p",
            ".contents p",
            ".entry-content p",
            ".post-content p",
            "main p",
            "article p",
        ]

        texts = []
        seen_texts = set()

        for selector in selectors:
            paragraphs = soup.select(selector)
            if not paragraphs:
                continue

            for p in paragraphs:
                text = " ".join(p.get_text(" ", strip=True).split())
                lower = text.lower()

                if not text:
                    continue
                if len(text) < 40:
                    continue

                if any(bad in lower for bad in [
                    "admission",
                    "closed",
                    "opening hours",
                    "ticket",
                    "access",
                    "contact",
                    "facebook",
                    "instagram",
                    "x.com",
                    "twitter",
                    "copyright",
                    "museum collection",
                ]):
                    continue

                if text in seen_texts:
                    continue

                seen_texts.add(text)
                texts.append(text)

            if len(texts) >= 2:
                break

        if texts:
            print(f"[MOT] Detail description found: {len(texts)} paragraphs")
        else:
            print(f"[MOT] No detail description found: {detail_url}")

        return texts[:6]

    def resolve_mot_image(item, detail_url, title):
        """
        图片优先级：
        1. imagePc
        2. imageSp
        3. detail page 正文图
        4. detail page meta 图（但会跳过通用 og-image）
        5. 空字符串
        """
        raw_candidates = [
            item.get("imagePc", ""),
            item.get("imageSp", ""),
        ]

        for raw in raw_candidates:
            abs_url = make_absolute(str(raw).strip())
            if is_valid_image(abs_url):
                print(f"[MOT] Image from JSON: {title} -> {abs_url}")
                return abs_url

        detail_img = fetch_detail_page_image(detail_url)
        if is_valid_image(detail_img):
            print(f"[MOT] Image from detail page: {title} -> {detail_img}")
            return detail_img

        print(f"[MOT] No valid image found: {title}")
        return fallback_image

    def should_skip_mot_title(title):
        return False

    def add_entry(item, label):
        nonlocal start_id

        title = clean_title(item.get("title", ""))
        if not title:
            return

        if should_skip_mot_title(title):
            print(f"[MOT] Skipping non-standard exhibition: {title}")
            return

        key = normalize_text(title)
        if key in seen_titles:
            print(f"[MOT] Skipping duplicate title: {title}")
            return
        seen_titles.add(key)

        permalink = str(item.get("permalink", "")).strip()
        if not permalink:
            print(f"[MOT] Skipping item without permalink: {title}")
            return

        detail_url = make_absolute(permalink)
        image_url = resolve_mot_image(item, detail_url, title)
        raw_description = fetch_detail_description(detail_url)

        entry = {
            "id": start_id,
            "slug": make_slug(title),
            "title": title,
            "category": "Exhibition",
            "location": "Museum of Contemporary Art Tokyo (Kiba)",
            "venue": "Museum of Contemporary Art Tokyo",
            "date": build_date_text(item, label["start"], label["end"]) or "See source",
            "startDate": label["start"].isoformat() if label["start"] else "",
            "endDate": label["end"].isoformat() if label["end"] else "",
            "image": image_url,
            "access": "Kiba Station (Tokyo Metro Tozai Line), around 15 minutes on foot",
            "price": "",
            "bookingUrl": "",
            "source": "Museum of Contemporary Art Tokyo",
            "sourceUrl": detail_url,
            "tags": [],
            "area": "Kiba",
            "language": "en",
            "rawDescription": raw_description,
            "sources": ["Museum of Contemporary Art Tokyo"],
            "popularity": 0,
            "bookmarkCount": 0,
            "wentCount": 0,
            "commentCount": 0,
            "score": 0,
        }
        entry["score"] = calculate_exhibition_score(entry)

        exhibitions.append(entry)
        print(f"[MOT] Added exhibition #{start_id}: {title}")
        print(f"[MOT] Final image: {entry['image'] or '(empty)'}")
        start_id += 1

    filtered = []
    for item in items:
        if not isinstance(item, dict):
            continue

        start_date = to_date(item.get("start"))
        end_date = to_date(item.get("end")) or start_date

        if not start_date:
            continue

        if end_date and end_date < today:
            continue

        is_current = start_date <= today <= end_date
        is_upcoming = start_date > today

        if is_current or is_upcoming:
            filtered.append((item, {"start": start_date, "end": end_date}))

    filtered.sort(key=lambda it: it[1]["start"] or today)

    print(f"[MOT] Filtered items count: {len(filtered)}")

    for item, label in filtered:
        add_entry(item, label)

    print(f"[MOT] Returning {len(exhibitions)} exhibitions")
    return exhibitions