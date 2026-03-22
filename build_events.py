import json
import re
import math
import os
import sys
import time
from openai import OpenAI

RAW_INPUT_PATH = "data/raw_events.json"
OUTPUT_PATH = "data/generated_events.json"
BUILD_SELF_LOCK_FILE = "build_events_self.lock"


def ensure_single_build_instance():
    if os.path.exists(BUILD_SELF_LOCK_FILE):
        print("=== build_events.py aborted (self lock exists) ===")
        sys.exit(0)

    with open(BUILD_SELF_LOCK_FILE, "w", encoding="utf-8") as f:
        f.write(f"pid={os.getpid()} started_at={time.time()}\n")


def cleanup_build_lock():
    if os.path.exists(BUILD_SELF_LOCK_FILE):
        os.remove(BUILD_SELF_LOCK_FILE)


def get_client() -> OpenAI:
    return OpenAI()


def sanitize_text(value) -> str:
    if value is None:
        return ""

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return ""
        value = str(value)

    if isinstance(value, list):
        value = "\n\n".join(sanitize_text(x) for x in value if sanitize_text(x))
    elif not isinstance(value, str):
        value = str(value)

    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", value)
    value = re.sub(r"[\ud800-\udfff]", "", value)
    value = value.encode("utf-8", "ignore").decode("utf-8")

    return value.strip()


def safe_json_check(payload):
    json.dumps(payload, ensure_ascii=False, allow_nan=False)


def debug_bad_item(item, prompt):
    print("\n========== BAD ITEM DEBUG ==========")
    print("TITLE:", repr(item.get("title")))
    print("VENUE:", repr(item.get("venue")))
    print("DATE:", repr(item.get("date")))
    print("LOCATION:", repr(item.get("location")))
    print("RAW DESCRIPTION TYPE:", type(item.get("rawDescription")))
    raw_preview = raw_description_text(item)
    print("RAW DESCRIPTION PREVIEW:", repr(raw_preview[:1000]))
    print("PROMPT LENGTH:", len(prompt))
    print("PROMPT PREVIEW:", repr(prompt[:1500]))
    print("====================================\n")


PROMPT_TEMPLATE_PRIORITY = """
You are a senior editor for a high-quality Tokyo exhibitions guide.

Your job is NOT to rewrite the text.
Your job is to identify what makes this exhibition DISTINCT and translate that into sharp editorial content.

INPUT:
- Title: {title}
- Venue: {venue}
- Date: {date}
- Location: {location}
- Official Exhibition Text:
{raw_description}

STEP 1 — UNDERSTAND (do internally, do NOT output):
- What is the most distinctive element?
  (e.g. scale, material, method, curatorial structure, artist approach)
- What is NOT generic about this exhibition?

STEP 2 — WRITE:

1. summary
- one sentence
- max 18 words
- MUST include ONE specific distinguishing feature
- avoid generic phrases completely

2. description
- exactly 2 short paragraphs
- paragraph 1: what is visually or structurally distinctive (be concrete)
- paragraph 2: what kind of viewing experience or impression it creates
- avoid filler transitions and generic tone

3. highlights
- 3 to 5 bullet points
- use 5 only if all are specific and high-value
- do NOT add filler just to reach a higher count
- each highlight should be 12 to 18 words
- MUST be specific and concrete
- each highlight should include:
  - a clear artistic element, method, structure, or subject
  - AND what it does or how it functions
- prefer:
  - artistic method
  - scale / material / technique
  - curatorial structure
  - exhibition format
- avoid generic medium-only phrases
- write each highlight as a clean editorial sentence

Prefer concise editorial sentences over short fragments.

STRICT RULES:
- Do NOT invent facts
- Do NOT mention date, venue, location in highlights
- Do NOT convert general statements into specific visual details unless explicitly stated
- If the source mentions scale, describe scale generally; do not exaggerate
- Do NOT introduce techniques or elements not explicitly mentioned
- DO NOT use generic phrases like:
  "explore", "experience", "discover",
  "humanity", "identity", "captivating",
  "remarkable", "focused look", "on view"
- DO NOT output vague phrases like:
  "strong emotional undertones"
- DO NOT output medium-only highlights like:
  "sculptural works on view", "painting-focused exhibition"
- Avoid generic expansion patterns such as:
  "creating a sense of", "offering insight into", "inviting viewers to"
- avoid empty expansion; longer highlights must remain grounded in the source text

OUTPUT JSON ONLY:
{{
  "summary": "...",
  "description": ["...", "..."],
  "highlights": ["...", "...", "..."]
}}
"""

PROMPT_TEMPLATE_SAFE = """
You are an editor for a Tokyo events website.

Write clear, grounded content based on the source text.

IMPORTANT:
- Prefer specific details (method, structure, approach)
- Avoid generic phrases
- Do NOT convert general statements into specific visual details unless explicitly stated

INPUT:
- Title: {title}
- Venue: {venue}
- Date: {date}
- Location: {location}
- Official Exhibition Text:
{raw_description}

TASK:

1. summary
- one sentence
- max 16 words
- include at least one concrete element if possible

2. description
- 1 to 2 short paragraphs
- stay close to source but avoid copying phrasing
- avoid generic editorial tone

3. highlights
- 3 to 5 bullet points
- prefer 3 if the source text is limited
- use more only when each point adds distinct value
- each highlight should be 12 to 18 words
- avoid generic phrases
- avoid medium-only phrases
- write each highlight as a complete sentence
- each highlight should include:
  - one concrete detail from the source
  - and one clear function, structure, or effect

Prefer concise editorial sentences over short fragments.

OUTPUT JSON ONLY:
{{
  "summary": "...",
  "description": ["..."],
  "highlights": ["...", "..."]
}}
"""


def generate_slug(text: str) -> str:
    text = (text or "").lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def normalize_list(value) -> list[str]:
    if isinstance(value, list):
        return [sanitize_text(x) for x in value if sanitize_text(x)]
    if isinstance(value, str) and sanitize_text(value):
        return [sanitize_text(value)]
    return []


def normalize_description(value) -> list[str]:
    return normalize_list(value)


def normalize_category(value: str) -> str:
    text = sanitize_text(value).lower()

    mapping = {
        "exhibition": "Exhibition",
        "exhibitions": "Exhibition",
        "film": "Film",
        "films": "Film",
        "movie": "Film",
        "movies": "Film",
        "cinema": "Film",
        "nightlife": "Nightlife",
        "club": "Nightlife",
        "clubs": "Nightlife",
        "party": "Nightlife",
        "parties": "Nightlife",
        "dj event": "Nightlife",
        "dj events": "Nightlife",
        "live": "Nightlife",
        "event": "Activity",
        "events": "Activity",
        "activity": "Activity",
        "activities": "Activity",
    }

    return mapping.get(text, "Activity")


def normalize_raw_description(raw) -> str:
    if isinstance(raw, list):
        parts = [sanitize_text(x) for x in raw]
        parts = [x for x in parts if x]
        return "\n\n".join(parts)

    if isinstance(raw, str):
        return sanitize_text(raw)

    return sanitize_text(raw)


def raw_description_text(item) -> str:
    return normalize_raw_description(item.get("rawDescription"))


def normalize_final_event(item: dict) -> dict:
    return {
        "id": item.get("id"),
        "slug": sanitize_text(item.get("slug")),
        "title": sanitize_text(item.get("title")),
        "category": normalize_category(item.get("category")),
        "location": sanitize_text(item.get("location")),
        "venue": sanitize_text(item.get("venue")),
        "date": sanitize_text(item.get("date")),
        "image": sanitize_text(item.get("image")),
        "summary": sanitize_text(item.get("summary")),
        "description": normalize_description(item.get("description")),
        "highlights": normalize_list(item.get("highlights")),
        "access": sanitize_text(item.get("access")),
        "source": sanitize_text(item.get("source")),
        "sourceUrl": sanitize_text(item.get("sourceUrl")),
        "price": sanitize_text(item.get("price")),
        "bookingUrl": sanitize_text(item.get("bookingUrl")),
        "startDate": sanitize_text(item.get("startDate")),
        "endDate": sanitize_text(item.get("endDate")),
        "tags": normalize_list(item.get("tags")),
        "area": sanitize_text(item.get("area")),
        "language": sanitize_text(item.get("language")) or "en",
        "needsReview": bool(item.get("needsReview", False)),
        "publishable": bool(item.get("publishable", True)),
        "qualityScore": int(item.get("qualityScore", 0) or 0),
        "qualityReasons": normalize_list(item.get("qualityReasons")),
    }


def validate_final_event_schema(item: dict):
    required_fields = [
        "id", "slug", "title", "category", "location", "venue", "date",
        "image", "summary", "description", "highlights",
        "access", "source", "sourceUrl",
        "needsReview", "publishable", "qualityScore", "qualityReasons"
    ]

    for field in required_fields:
        if field not in item:
            raise ValueError(f"Missing final schema field: {field}")

    if item["category"] not in {"Exhibition", "Film", "Nightlife", "Activity"}:
        raise ValueError(f"Invalid category: {item['category']}")

    if not isinstance(item["description"], list):
        raise ValueError("description must be a list")

    if not isinstance(item["highlights"], list):
        raise ValueError("highlights must be a list")

    if not isinstance(item["qualityReasons"], list):
        raise ValueError("qualityReasons must be a list")


def load_raw_events():
    with open(RAW_INPUT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_events(events):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def validate_event(item):
    required_fields = ["title", "venue", "date", "location", "rawDescription"]
    for f in required_fields:
        if not item.get(f):
            print(f"⚠️ Missing field: {f} in {item.get('title')}")


def is_high_priority(item) -> bool:
    title = (item.get("title") or "").lower()
    raw = raw_description_text(item)

    priority_keywords = [
        "mueck",
        "ron mueck",
        "roppongi crossing",
        "wyeth",
        "orsay",
        "british museum",
        "monet",
        "picasso",
        "mariko mori",
        "eric carle",
        "tate",
    ]

    if any(keyword in title for keyword in priority_keywords):
        return True

    if len(raw) >= 500:
        return True

    return False


def build_prompt(item):
    template = PROMPT_TEMPLATE_PRIORITY if is_high_priority(item) else PROMPT_TEMPLATE_SAFE

    return template.format(
        title=sanitize_text(item.get("title", "")),
        venue=sanitize_text(item.get("venue", "")),
        date=sanitize_text(item.get("date", "")),
        location=sanitize_text(item.get("location", "")),
        raw_description=sanitize_text(raw_description_text(item)),
    )


def fallback_summary(item) -> str:
    title = item.get("title", "This exhibition")
    raw = raw_description_text(item).lower()

    if "scale" in raw:
        return f"{title} centers on scale as a way of unsettling perception."
    if "archival" in raw:
        return f"{title} uses archival research and video to connect history with the present."
    if "time" in raw:
        return f"{title} uses time as a framework across multiple artistic practices."
    if "video" in raw:
        return f"{title} presents video-based work shaped by research and performance."

    return f"{title} is defined by a clear contemporary artistic approach."


def fallback_description(item) -> list[str]:
    raw = raw_description_text(item).lower()
    title = item.get("title", "This exhibition")

    if "scale" in raw and "sculpture" in raw:
        return [
            "Ron Mueck’s figurative sculptures use shifts in scale to unsettle how the body is seen and understood.",
            "Their realism and ambiguity create a viewing experience that feels immediate, strange, and intensely focused."
        ]

    if "every three years" in raw or "twenty-one artists" in raw:
        return [
            "This edition of Roppongi Crossing brings together 21 artists and collectives as a wide-angle view of Japan’s contemporary art scene.",
            "With time as its central framework, the exhibition expands across multiple forms, from painting and video to crafts and community-based practice."
        ]

    if "archival research" in raw and "personal interviews" in raw:
        return [
            "Hao Jingban’s video works draw on archival research, personal interviews, and performance to connect lived experience with historical record.",
            "The exhibition traces how individual stories and larger historical forces continue to echo into the present."
        ]

    if "time" in raw:
        return [
            f"{title} is structured around questions of time, change, and continuity.",
            "Its presentation brings together multiple perspectives in a clear but layered way."
        ]

    if "video" in raw:
        return [
            f"{title} centers on video-based work shaped by research and careful narrative construction.",
            "The result is a measured viewing experience grounded in detail rather than spectacle."
        ]

    return [
        f"{title} presents a contemporary exhibition shaped by a clear artistic approach.",
        "The presentation emphasizes the structure and method that distinguish the work."
    ]


def fallback_highlights(item) -> list[str]:
    raw = raw_description_text(item).lower()
    highlights = []

    if "scale" in raw:
        highlights.append("Manipulation of scale alters bodily perception")
    if "figurative sculpture" in raw or "sculpture" in raw:
        highlights.append("Figurative sculpture with intense physical presence")
    if "ambiguity" in raw or "individual reflection" in raw:
        highlights.append("Ambiguity leaves space for individual interpretation")
    if "fondation cartier" in raw or "traveling" in raw or "milan" in raw or "seoul" in raw:
        highlights.append("Part of a major international touring exhibition")

    if "every three years" in raw or "staged every three years" in raw:
        highlights.append("Triennial survey of Japan’s contemporary art scene")
    if "twenty-one artists" in raw or "artist groups" in raw:
        highlights.append("Brings together 21 artists and collectives")
    if "guest curators" in raw:
        highlights.append("Co-curated with internationally active guest curators")
    if "theme of 'time'" in raw or "theme of time" in raw:
        highlights.append("Built around time as a curatorial theme")
    if "crafts" in raw or "community projects" in raw:
        highlights.append("Extends beyond painting and sculpture")

    if "archival research" in raw:
        highlights.append("Archival research shapes the work’s structure")
    if "personal interviews" in raw:
        highlights.append("Personal interviews intersect with historical material")
    if "performance" in raw:
        highlights.append("Performance informs the video-based approach")
    if "individual and collective stories" in raw:
        highlights.append("Individual and collective stories are closely interwoven")
    if "present and past" in raw or "distance between present and past" in raw:
        highlights.append("Examines the distance between past and present")

    deduped = []
    for h in highlights:
        if h not in deduped:
            deduped.append(h)

    return deduped[:5]


def clean_highlights(highlights):
    banned_keywords = [
        "located at",
        "located in",
        "runs from",
        "april", "may", "june", "july",
        "august", "september", "october",
        "november", "december", "january",
        "february", "march",
        "museum", "station", "roppongi", "tokyo",
        "presented at", "on view",
    ]

    banned_exact = [
        "Sculptural works on view",
        "Painting-focused exhibition",
        "Strong emotional undertones",
        "Focused look at distinctive artistic practice",
        "Reflection on memory",
        "Themes of time and memory",
        "Moving image-based work",
        "Performance-based practice",
    ]

    weak_highlight_patterns = [
        "personal reflection",
        "emotional depth",
        "multiple perspectives",
        "cultural lenses",
        "layered viewing experience",
    ]

    cleaned = []
    for h in highlights:
        text = sanitize_text(h)
        lower = text.lower()

        if not text:
            continue
        if text in banned_exact:
            continue
        if any(keyword in lower for keyword in banned_keywords):
            continue
        if any(p in lower for p in weak_highlight_patterns):
            continue
        if len(text.split()) <= 2:
            continue

        cleaned.append(text)

    deduped = []
    for h in cleaned:
        if h not in deduped:
            deduped.append(h)

    return deduped[:5]


def contains_invented_detail(text: str) -> bool:
    risky_terms = [
        "projection",
        "projections",
        "soundscape",
        "soundscapes",
        "interactive",
        "tactile",
        "shadow",
        "shadows",
        "lighting",
        "light patterns",
        "paper sculptures",
        "video projections",
    ]
    lower = (text or "").lower()
    return any(term in lower for term in risky_terms)


def is_risky_output(ai):
    full_text = " ".join([
        ai.get("summary", ""),
        " ".join(ai.get("description", [])),
        " ".join(ai.get("highlights", [])),
    ])
    return contains_invented_detail(full_text)


def has_unsupported_detail(ai, item):
    raw = raw_description_text(item).lower()
    text = " ".join([
        ai.get("summary", ""),
        " ".join(ai.get("description", [])),
        " ".join(ai.get("highlights", [])),
    ]).lower()

    suspicious_terms = []

    if "larger-than-life" in text and "larger-than-life" not in raw:
        suspicious_terms.append("larger-than-life")
    if "strikingly small" in text and "strikingly small" not in raw:
        suspicious_terms.append("strikingly small")
    if "oversized" in text and "oversized" not in raw:
        suspicious_terms.append("oversized")
    if "miniature" in text and "miniature" not in raw:
        suspicious_terms.append("miniature")
    if "archival footage" in text and "archival footage" not in raw:
        suspicious_terms.append("archival footage")
    if "contemporary video techniques" in text and "contemporary video techniques" not in raw:
        suspicious_terms.append("contemporary video techniques")
    if "lifelike presence" in text and "sense of life" not in raw and "lifelike presence" not in raw:
        suspicious_terms.append("lifelike presence")
    if "minuscule" in text and "minuscule" not in raw:
        suspicious_terms.append("minuscule")
    if "monumental" in text and "monumental" not in raw:
        suspicious_terms.append("monumental")
    if "video installations" in text and "video installations" not in raw:
        suspicious_terms.append("video installations")
    if "participation and connection" in text and "participation and connection" not in raw:
        suspicious_terms.append("participation and connection")

    if suspicious_terms:
        print(f"⚠️ Unsupported detail detected: {item.get('title')} -> {suspicious_terms}")

    return len(suspicious_terms) > 0


def parse_ai_json(content: str):
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```json\s*|^```\s*|```$", "", content, flags=re.MULTILINE).strip()
    return json.loads(content)


def generate_ai_content(client: OpenAI, item):
    prompt = sanitize_text(build_prompt(item))
    model_name = "gpt-4o" if is_high_priority(item) else "gpt-4o-mini"

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    try:
        safe_json_check(
            {
                "model": model_name,
                "messages": messages,
                "temperature": 0.2,
            }
        )
    except Exception as e:
        print(f"❌ Local JSON check failed for: {item.get('title')}")
        debug_bad_item(item, prompt)
        print("JSON ERROR:", repr(e))
        print("SANITIZED PROMPT LENGTH:", len(sanitize_text(prompt)))
        return {
            "summary": fallback_summary(item),
            "description": fallback_description(item),
            "highlights": fallback_highlights(item),
            "_status": "fallback_error",
        }

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.2,
        )
    except Exception as e:
        print(f"❌ API request failed for: {item.get('title')}")
        debug_bad_item(item, prompt)
        print("API ERROR:", repr(e))

        # 二次兜底：把 prompt 截断后再试一次
        try:
            short_prompt = sanitize_text(prompt[:12000])
            short_messages = [
                {
                    "role": "user",
                    "content": short_prompt,
                }
            ]

            response = client.chat.completions.create(
                model=model_name,
                messages=short_messages,
                temperature=0.2,
            )
        except Exception as e2:
            print(f"❌ Retry API request failed for: {item.get('title')}")
            print("RETRY API ERROR:", repr(e2))
            return {
                "summary": fallback_summary(item),
                "description": fallback_description(item),
                "highlights": fallback_highlights(item),
                "_status": "fallback_error",
            }

    content = sanitize_text(response.choices[0].message.content or "")

    try:
        parsed = parse_ai_json(content)

        description = parsed.get("description", [])
        if isinstance(description, str):
            description = [description]
        elif not isinstance(description, list):
            description = []

        highlights = clean_highlights(parsed.get("highlights", []))

        return {
            "summary": sanitize_text(parsed.get("summary", "")),
            "description": [sanitize_text(x) for x in description if sanitize_text(x)],
            "highlights": [sanitize_text(x) for x in highlights if sanitize_text(x)],
            "_status": "ok",
        }
    except Exception:
        print("❌ JSON parse failed for:", item.get("title"))
        print(content)
        return {
            "summary": fallback_summary(item),
            "description": fallback_description(item),
            "highlights": fallback_highlights(item),
            "_status": "fallback_error",
        }

def evaluate_quality(ai, item):
    score = 0
    reasons = []

    summary = sanitize_text(ai.get("summary", ""))
    description = [sanitize_text(x) for x in ai.get("description", []) if sanitize_text(x)]
    highlights = [sanitize_text(x) for x in ai.get("highlights", []) if sanitize_text(x)]
    full_text = " ".join([summary] + description + highlights).lower()

    if summary:
        score += 1
    else:
        reasons.append("missing_summary")

    if len(description) >= 2:
        score += 1
    else:
        reasons.append("weak_description_structure")

    if len(highlights) >= 2:
        score += 1
    else:
        reasons.append("too_few_highlights")

    distinct_keywords = [
        "scale",
        "archival",
        "guest curators",
        "community projects",
        "figurative sculpture",
        "performance",
        "personal interviews",
        "historical narratives",
        "time",
        "collective stories",
        "fondation cartier",
    ]
    distinct_signals = sum(1 for kw in distinct_keywords if kw in full_text)

    if distinct_signals >= 1:
        score += 1
    else:
        reasons.append("not_distinct_enough")

    hard_bad_patterns = [
        "thought-provoking",
        "immersive",
        "focused look",
        "on view",
        "humanity",
        "identity",
        "human experience",
        "captivating",
        "remarkable",
    ]
    for p in hard_bad_patterns:
        if p in full_text:
            score -= 1
            reasons.append(f"generic_phrase:{p}")

    soft_template_patterns = [
        "rich tapestry",
        "multifaceted exploration",
        "dynamic environment",
        "deeper appreciation",
        "fluidity of time",
        "multi-dimensional",
        "transcend conventional boundaries",
        "immersive experience",
        "thought-provoking experience",
        "invites viewers",
        "inviting viewers",
        "encourages reflection",
        "encouraging reflection",
    ]
    for p in soft_template_patterns:
        if p in full_text:
            score -= 1
            reasons.append(f"soft_template:{p}")

    if has_unsupported_detail(ai, item):
        score -= 2
        reasons.append("unsupported_detail")

    if is_risky_output(ai):
        score -= 2
        reasons.append("risky_output")

    highlight_text = " ".join(highlights).lower()
    highlight_signal_keywords = [
        "scale",
        "archival",
        "guest curators",
        "community projects",
        "fondation cartier",
        "personal interviews",
        "performance",
        "collective stories",
        "time",
    ]

    if len(highlights) >= 4 and any(kw in highlight_text for kw in highlight_signal_keywords):
        score += 1

    has_generic_phrase = any(r.startswith("generic_phrase:") for r in reasons)
    has_unsupported = "unsupported_detail" in reasons
    has_risky = "risky_output" in reasons

    publishable = score >= 2

    needs_review = (
        score < 4
        or has_generic_phrase
        or has_unsupported
        or has_risky
    )

    return {
        "qualityScore": score,
        "needsReview": needs_review,
        "publishable": publishable,
        "qualityReasons": reasons,
    }


def pick_best_result(results, item):
    scored = []

    for ai in results:
        quality = evaluate_quality(ai, item)
        scored.append((ai, quality))

    ok_items = [(ai, q) for ai, q in scored if ai.get("_status") == "ok"]
    fallback_items = [(ai, q) for ai, q in scored if ai.get("_status") != "ok"]

    def rank_pair(pair):
        ai, q = pair
        reasons = q.get("qualityReasons", [])
        generic_count = sum(1 for r in reasons if r.startswith("generic_phrase:"))
        soft_count = sum(1 for r in reasons if r.startswith("soft_template:"))
        return (
            q["publishable"],
            -generic_count,
            -soft_count,
            q["qualityScore"],
        )

    if ok_items:
        return max(ok_items, key=rank_pair)

    return max(fallback_items, key=rank_pair)


def enrich_event(client: OpenAI, item, index):
    title = item.get("title", "")
    print(f"⚙️ Generating: {title}")

    attempts = 4 if is_high_priority(item) else 2
    candidates = []

    for _ in range(attempts):
        ai = generate_ai_content(client, item)
        candidates.append(ai)

    best_ai, best_quality = pick_best_result(candidates, item)

    if not best_quality["publishable"]:
        print(
            f"⚠️ Not publishable yet: {title} | "
            f"score={best_quality['qualityScore']} | "
            f"reasons={best_quality['qualityReasons']}"
        )

    enriched = {
        "id": item.get("id", 7000 + index),
        "slug": item.get("slug") or generate_slug(title),
        "title": title,
        "category": item.get("category", "Activity"),
        "location": item.get("location"),
        "venue": item.get("venue"),
        "date": item.get("date"),
        "image": item.get("image"),
        "summary": best_ai.get("summary", ""),
        "description": best_ai.get("description", []),
        "highlights": best_ai.get("highlights", []),
        "access": item.get("access", ""),
        "source": item.get("source"),
        "sourceUrl": item.get("sourceUrl"),
        "price": item.get("price", ""),
        "bookingUrl": item.get("bookingUrl", ""),
        "startDate": item.get("startDate", ""),
        "endDate": item.get("endDate", ""),
        "tags": item.get("tags", []),
        "area": item.get("area", ""),
        "language": item.get("language", "en"),
        "needsReview": best_quality["needsReview"],
        "publishable": best_quality["publishable"],
        "qualityScore": best_quality["qualityScore"],
        "qualityReasons": best_quality["qualityReasons"],
    }

    return normalize_final_event(enriched)


def dedupe_events(events):
    best_by_source = {}

    for event in events:
        key = event.get("sourceUrl") or event.get("slug") or str(event.get("id"))
        current = best_by_source.get(key)

        if current is None:
            best_by_source[key] = event
            continue

        current_publishable = current.get("publishable", False)
        new_publishable = event.get("publishable", False)

        if new_publishable and not current_publishable:
            best_by_source[key] = event
            continue

        if new_publishable == current_publishable:
            if event.get("qualityScore", 0) > current.get("qualityScore", 0):
                best_by_source[key] = event

    return list(best_by_source.values())


def main():
    ensure_single_build_instance()

    try:
        print(f"BUILD START pid={os.getpid()} at {time.time()}")

        client = get_client()
        raw_events = load_raw_events()

        final_events = []
        for i, item in enumerate(raw_events):
            try:
                validate_event(item)
                enriched = enrich_event(client, item, i)
                final_events.append(enriched)
            except Exception as e:
                print(f"⚠️ Failed to enrich event {item.get('title', 'Unknown')}: {e}")
                continue

        final_events = dedupe_events(final_events)

        valid_events = []
        for event in final_events:
            try:
                validate_final_event_schema(event)
                valid_events.append(event)
            except ValueError as e:
                print(f"⚠️ Skipping invalid event {event.get('title', 'Unknown')}: {e}")

        final_events = valid_events

        save_events(final_events)
        print(f"\n✅ Done! Generated {len(final_events)} deduped events → {OUTPUT_PATH}")

    finally:
        cleanup_build_lock()


if __name__ == "__main__":
    main()