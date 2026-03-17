from utils.common_utils import normalize_text

# =========================
# 展览评分相关
# =========================

def source_weight_for_sources(sources):
    """
    根据来源列表计算来源权重。
    """
    weights = {
        "Mori Art Museum": 25,
        "Tokyo Metropolitan Art Museum": 24,
        "Museum of Contemporary Art Tokyo": 24,
        "Tokyo National Museum": 24,
    }
    return sum(weights.get(s, 0) for s in sources)


def calculate_exhibition_score(item):
    """
    展览评分规则（当前版本不考虑时效性）：
        score = 来源权重 + 场馆权重 + 热度权重

    热度权重参考字段：
    - popularity
    - bookmarkCount
    - wentCount
    - commentCount
    """
    venue_weight_map = {
        "mori art museum": 30,
        "museum of contemporary art tokyo": 26,
        "tokyo metropolitan art museum": 24,
        "tokyo national museum": 24,
    }

    venue_name = normalize_text(item.get("venue", ""))
    venue_weight = venue_weight_map.get(venue_name, 10)

    popularity = item.get("popularity", 0) or 0
    bookmark_count = item.get("bookmarkCount", 0) or 0
    went_count = item.get("wentCount", 0) or 0
    comment_count = item.get("commentCount", 0) or 0

    heat_score = 0
    heat_score += min(int(popularity), 20)
    heat_score += min(int(bookmark_count) // 5, 10)
    heat_score += min(int(went_count) // 5, 10)
    heat_score += min(int(comment_count) * 2, 10)

    sources = item.get("sources", [])
    source_score = source_weight_for_sources(sources)

    return source_score + venue_weight + heat_score