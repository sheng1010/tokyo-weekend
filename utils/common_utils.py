# =========================
# Common helpers
# =========================


def normalize_text(s):
    if not s:
        return ""

    return " ".join(
        str(s).lower()
        .replace("“", '"')
        .replace("”", '"')
        .replace("’", "'")
        .split()
    )


def repair_text_encoding(value):
    if not isinstance(value, str) or not value:
        return value

    suspicious = ("Ã", "Â", "â", "æ", "ï", "¤", "£", "¡")
    if not any(token in value for token in suspicious):
        return value

    try:
        repaired = value.encode("latin-1").decode("utf-8")
        return repaired or value
    except Exception:
        return value
