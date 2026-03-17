from utils.common_utils import normalize_text
from utils.score_utils import calculate_exhibition_score

# =========================
# 多来源展览合并
# =========================

def merge_exhibitions(*lists):
    """
    合并多个展览来源并按标题 + 场馆去重。
    """
    merged = {}

    for exhibition_list in lists:
        for item in exhibition_list:
            key = (
                normalize_text(item.get("title", "")),
                normalize_text(item.get("venue", "")) or normalize_text(item.get("location", "")),
            )

            if key not in merged:
                merged[key] = item.copy()
                continue

            existing = merged[key]

            existing_sources = set(existing.get("sources", []))
            new_sources = set(item.get("sources", []))
            existing["sources"] = sorted(existing_sources | new_sources)

            if not existing.get("image") and item.get("image"):
                existing["image"] = item["image"]

            if not existing.get("venue") and item.get("venue"):
                existing["venue"] = item["venue"]

            if not existing.get("description") and item.get("description"):
                existing["description"] = item["description"]

            if not existing.get("sourceUrl") and item.get("sourceUrl"):
                existing["sourceUrl"] = item["sourceUrl"]

            existing["popularity"] = max(existing.get("popularity", 0), item.get("popularity", 0))
            existing["bookmarkCount"] = max(existing.get("bookmarkCount", 0), item.get("bookmarkCount", 0))
            existing["wentCount"] = max(existing.get("wentCount", 0), item.get("wentCount", 0))
            existing["commentCount"] = max(existing.get("commentCount", 0), item.get("commentCount", 0))

    result = list(merged.values())

    for item in result:
        item["score"] = calculate_exhibition_score(item)

    result.sort(key=lambda x: x["score"], reverse=True)
    return result