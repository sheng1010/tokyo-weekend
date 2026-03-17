# =========================
# 通用工具函数
# =========================

def safe_get(dct, path, default=""):
    """
    安全地从嵌套 dict 中取值。

    例：
        safe_get(item, ["venue", "fields", "fullName"], "Tokyo")
    """
    current = dct
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def normalize_text(s):
    """
    文本标准化：
    - 转小写
    - 统一引号
    - 去掉多余空格

    用于去重时生成 key。
    """
    if not s:
        return ""

    return " ".join(
        str(s).lower()
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .split()
    )