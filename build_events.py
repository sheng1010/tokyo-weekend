import json
import re
import math
import os
import sys
import time
from openai import OpenAI

from utils.common_utils import repair_text_encoding

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="backslashreplace",
        line_buffering=True,
    )
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="backslashreplace",
        line_buffering=True,
    )

RAW_INPUT_PATH = "data/raw_events.json"
OUTPUT_PATH = "data/generated_events.json"
BUILD_SELF_LOCK_FILE = "build_events_self.lock"
NORMAL_AI_ATTEMPTS = max(1, int(os.environ.get("TOKYOWEEKEND_AI_ATTEMPTS_NORMAL", "1")))
HIGH_PRIORITY_AI_ATTEMPTS = max(1, int(os.environ.get("TOKYOWEEKEND_AI_ATTEMPTS_HIGH", "2")))


def parse_lock_pid(lock_path: str) -> int | None:
    try:
        with open(lock_path, "r", encoding="utf-8") as f:
            contents = f.read()
    except OSError:
        return None

    match = re.search(r"pid=(\d+)", contents)
    if not match:
        return None

    try:
        return int(match.group(1))
    except ValueError:
        return None


def process_is_alive(pid: int | None) -> bool:
    if not pid:
        return False

    try:
        os.kill(pid, 0)
    except OSError:
        return False

    return True


def ensure_single_build_instance():
    if os.path.exists(BUILD_SELF_LOCK_FILE):
        existing_pid = parse_lock_pid(BUILD_SELF_LOCK_FILE)

        if process_is_alive(existing_pid):
            print(
                "=== build_events.py aborted (self lock exists) === "
                f"active_pid={existing_pid}"
            )
            sys.exit(0)

        print(
            "=== removing stale build_events self lock === "
            f"stale_pid={existing_pid or 'unknown'}"
        )
        cleanup_build_lock()

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

    return repair_text_encoding(value.strip())


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
You are a senior editor for a high-quality Tokyo events guide.

Your job is NOT to rewrite the text.
Your job is to identify what makes this event DISTINCT and translate that into sharp editorial content.

INPUT:
- Title: {title}
- Category: {category}
- Venue: {venue}
- Date: {date}
- Location: {location}
- Official Event Text:
{raw_description}

STEP 1 — UNDERSTAND (do internally, do NOT output):
- What is the most distinctive element?
  (e.g. scale, material, method, curatorial structure, artist approach)
- What is NOT generic about this event?

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
  - a clear element, structure, or subject
  - AND what it does or how it functions
- prefer:
  - program structure
  - lineup / format / setting
  - curatorial or editorial structure
  - event format
- avoid generic category-only phrases
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
- DO NOT output category-only highlights like:
  "late-night event", "music event", "festival listing"
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
- Category: {category}
- Venue: {venue}
- Date: {date}
- Location: {location}
- Official Event Text:
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


EDITORIAL_PROMPT_TEMPLATE_PRIORITY = """
You are a senior editor for a high-quality Tokyo recommendation site.

Your job is to identify what makes this listing distinct and turn it into sharp editorial copy.
Do not write like a venue marketer, a tourism brochure, or a database entry.

GLOBAL EDITORIAL RULES:
{editorial_rules}

CATEGORY-SPECIFIC DIRECTION:
{category_guidance}

INPUT:
- Title: {title}
- Category: {category}
- Venue: {venue}
- Date: {date}
- Location: {location}
- Official Event Text:
{raw_description}
{extra_context}

WRITE:

1. summary
- exactly one sentence
- max 18 words
- lead with the actual hook, not the schedule
- make it sound like a recommendation line, not a listing label

2. description
- exactly 2 short paragraphs
- paragraph 1: what makes it concretely distinctive
- paragraph 2: why it is worth choosing now
- do not repeat title/date/venue unless essential
- do not write brochure filler or neutral database prose

3. highlights
- 3 to 4 bullet points
- every bullet should read like a reason this specific listing matters
- each highlight should be 12 to 22 words
- make them specific enough that they would not fit a different listing

STRICT RULES:
- Do NOT invent facts
- Do NOT mention date, venue, or location in highlights unless essential to the hook
- Do NOT convert general statements into specific visual details unless explicitly stated
- Do NOT use generic phrases like:
  "explore", "experience", "discover", "humanity", "identity",
  "captivating", "remarkable", "focused look", "on view"
- Do NOT use brochure phrases like:
  "visitors can enjoy", "offers a chance to", "join us at",
  "this event features", "this exhibition uniquely combines"
- Avoid empty expansion patterns such as:
  "creating a sense of", "offering insight into", "inviting viewers to"

OUTPUT JSON ONLY:
{{
  "summary": "...",
  "description": ["...", "..."],
  "highlights": ["...", "...", "..."]
}}
"""

EDITORIAL_PROMPT_TEMPLATE_SAFE = """
You are an editor for a Tokyo recommendation site.

Write grounded, readable copy based on the source text.
The page already shows venue and date, so use the copy for editorial value rather than logistics.

GLOBAL EDITORIAL RULES:
{editorial_rules}

CATEGORY-SPECIFIC DIRECTION:
{category_guidance}

INPUT:
- Title: {title}
- Category: {category}
- Venue: {venue}
- Date: {date}
- Location: {location}
- Official Event Text:
{raw_description}
{extra_context}

TASK:

1. summary
- one sentence
- max 16 words
- lead with the most concrete hook available
- do not sound like a timetable or venue card

2. description
- 2 short paragraphs when possible
- stay close to source but rewrite into editorial prose
- paragraph 1 should identify the hook
- paragraph 2 should say why that hook matters

3. highlights
- 2 to 4 bullet points
- prefer fewer points over generic points
- each highlight should be a complete sentence
- each highlight must contain one concrete detail and one editorial reason it matters

OUTPUT JSON ONLY:
{{
  "summary": "...",
  "description": ["...", "..."],
  "highlights": ["...", "..."]
}}
"""

BASE_EDITORIAL_RULES = """
- Write like an experienced editor making a recommendation, not a neutral catalog entry.
- Prefer judgment, structure, tone, scale, lineup identity, or curatorial framing over logistics.
- Do not address the reader directly.
- Do not open with generic formulas such as "This event", "The event", "This exhibition", or "Visitors can".
- Avoid empty praise. If the source is thin, stay concise and concrete.
- Use proper nouns only when they actually sharpen the recommendation.
- Do not invent evaluative claims about performances, visuals, crowd response, or reputation unless the source clearly supports them.
- Avoid hype words such as "unforgettable", "breathtaking", "vibrant", "dynamic", "stellar", "must-see", and "immersive".
""".strip()


def build_category_guidance(item) -> str:
    category = normalize_category(item.get("category"))

    if category == "Film":
        return """
- Sound like a film editor recommending what makes the release worth seeing now.
- Prioritize directorial identity, cast chemistry, genre engine, adaptation angle, visual scale, or tonal hook.
- Do not just restate the premise line by line.
- Do not praise acting, visuals, or scale unless the source explicitly gives you evidence for that claim.
- Highlights should feel like reasons to book a ticket, not metadata.
- Description paragraph 2 should explain why it stands out within current theatrical releases.
""".strip()

    if category == "Nightlife":
        return """
- Sound like a nightlife editor who can picture the room, the floor, and the sonic direction.
- Prioritize guest DJs, crews, organizers, live acts, genre cues, and whether the night feels intimate, heavy, psychedelic, or headline-driven.
- Avoid logistics, dress-code style notes, and generic "good atmosphere" wording.
- Do not invent crowd response, seamless mixing, or sonic adjectives unless they are clearly grounded in the source text.
- Highlights should tell the reader who is shaping the night and what kind of room energy that implies.
- Description should read like a club recommendation, not an event announcement.
""".strip()

    if category == "Activity":
        return """
- Sound like a city editor recommending a specific seasonal or cultural outing.
- Prioritize the ritual, public spectacle, seasonal marker, competition, procession, flowers, illumination, or participatory format.
- Avoid generic sightseeing language and broad claims about culture.
- Do not sell the event with generic travel-copy adjectives; keep the recommendation grounded in what physically happens there.
- Highlights should make clear what actually happens there and why it is memorable in Tokyo's calendar.
- Description paragraph 2 should explain what makes this outing feel special rather than routine.
""".strip()

    return """
- Sound like an art editor or curator writing a recommendation.
- Prioritize medium, scale, research method, key works, curatorial structure, artist approach, or historical frame.
- Avoid empty museum language and generic claims about emotion or thoughtfulness.
- Do not inflate the exhibition with prestige adjectives unless the source directly supports them.
- Highlights should make clear what is materially or structurally specific to this exhibition.
- Description paragraph 2 should explain why the show is worth making time for now.
""".strip()


def build_extra_prompt_context(item) -> str:
    category = normalize_category(item.get("category"))
    extra_lines = []

    if category == "Film":
        director = sanitize_text(item.get("director", ""))
        cast = sanitize_text(item.get("cast", ""))
        if director:
            extra_lines.append(f"Director: {director}")
        if cast:
            extra_lines.append(f"Cast: {cast}")

    if category == "Nightlife":
        raw = raw_description_text(item)
        stop_patterns = [
            r"SPECIAL\s+GUEST(?:\s+DJ)?\s*:",
            r"GUEST\s+DJ\s*:",
            r"DJ(?:'S|鈥橲|閳ユ獨)?(?:\s*\(A\s*TO\s*Z\))?\s*:",
            r"LIVE\s*:",
            r"PHOTO\s*:",
            r"FOOD\s*:",
            r"ORGANIZER\s*:",
            r"\[[^\]]+\]\s+\w+\s+DJ\s*:",
        ]
        extracted = {
            "Guest DJ": extract_nightlife_segment(raw, [r"GUEST\s+DJ", r"SPECIAL\s+GUEST(?:\s+DJ)?"], stop_patterns),
            "DJ lineup": extract_nightlife_segment(raw, [r"DJ(?:'S|鈥橲|閳ユ獨)?(?:\s*\(A\s*TO\s*Z\))?"], stop_patterns),
            "Live": extract_nightlife_segment(raw, [r"LIVE"], stop_patterns),
            "Organizer": extract_nightlife_segment(raw, [r"ORGANIZER"], stop_patterns),
        }
        for label, value in extracted.items():
            cleaned = compact_spaces(value)
            if cleaned and looks_like_clean_lineup_segment(cleaned, 18):
                extra_lines.append(f"{label}: {cleaned}")

    if not extra_lines:
        return ""

    return "\n- Structured source notes:\n" + "\n".join(f"  - {line}" for line in extra_lines)


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
        "director": sanitize_text(item.get("director")),
        "cast": sanitize_text(item.get("cast")),
        "screeningVenues": item.get("screeningVenues", []),
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
            print(f"[WARN] Missing field: {f} in {item.get('title')}")


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
    template = (
        EDITORIAL_PROMPT_TEMPLATE_PRIORITY
        if is_high_priority(item)
        else EDITORIAL_PROMPT_TEMPLATE_SAFE
    )
    raw_text = sanitize_text(raw_description_text(item))
    extra_context = build_extra_prompt_context(item)

    return template.format(
        editorial_rules=BASE_EDITORIAL_RULES,
        category_guidance=build_category_guidance(item),
        title=sanitize_text(item.get("title", "")),
        category=sanitize_text(item.get("category", "")),
        venue=sanitize_text(item.get("venue", "")),
        date=sanitize_text(item.get("date", "")),
        location=sanitize_text(item.get("location", "")),
        raw_description=raw_text,
        extra_context=extra_context,
    )


def parse_cast_names(text: str) -> list[str]:
    cleaned = sanitize_text(text)
    cleaned = re.sub(r"^(Cast:|声の出演：|出演：)", "", cleaned).strip()
    if not cleaned:
        return []

    names = [sanitize_text(name) for name in re.split(r"[、,／/]", cleaned) if sanitize_text(name)]
    return names[:4]


def film_synopsis_parts(item) -> list[str]:
    raw = item.get("rawDescription", [])
    parts = normalize_list(raw)
    result = []
    for part in parts:
        lower = part.lower()
        if lower.startswith("director:") or lower.startswith("cast:"):
            continue
        result.append(part)
    return result


def film_synopsis_text(item) -> str:
    return " ".join(film_synopsis_parts(item)).strip()


def infer_film_hook(text: str) -> str:
    lower = sanitize_text(text).lower()
    keyword_hooks = [
        (["remake", "リメイク", "映画オタク", "actor", "俳優", "監督"], "a self-aware movie-industry setup with room for comedy and personality"),
        (["mystery", "謎", "discover", "encounter"], "a mystery hook that gives the story immediate forward motion"),
        (["battle", "war", "襲撃", "revenge", "討ち"], "high-stakes conflict rather than casual slice-of-life pacing"),
        (["friend", "team", "5人", "group"], "ensemble chemistry and group dynamics"),
        (["ocean", "sea", "undersea", "海"], "large-scale world-building and visual spectacle"),
        (["music", "song", "歌", "live", "concert"], "performance energy that should play well on a big screen"),
        (["ghost", "monster", "demon", "鬼"], "strong genre tension and a clearer horror-fantasy angle"),
        (["family", "child", "parent", "mother", "father"], "emotion driven by family relationships rather than pure plot mechanics"),
        (["journey", "trip", "travel", "train", "island", "camp"], "a travel or quest structure that keeps the film moving"),
    ]

    for keywords, hook in keyword_hooks:
        if any(keyword in lower for keyword in keywords):
            return hook

    return "a premise strong enough to make the film feel like more than a routine release"


def shorten_film_synopsis(text: str, max_chars=280) -> str:
    cleaned = sanitize_text(text)
    if not cleaned:
        return ""

    sentences = re.split(r"(?<=[。！？!?])\s*", cleaned)
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    picked = []
    for sentence in sentences:
        candidate = " ".join(picked + [sentence]).strip()
        if len(candidate) > max_chars and picked:
            break
        picked.append(sentence)
        if len(picked) >= 2:
            break

    summary = " ".join(picked).strip()
    if not summary:
        summary = cleaned[:max_chars].rstrip()

    return summary


def compact_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", sanitize_text(text)).strip()


def split_people(text: str, limit=4) -> list[str]:
    cleaned = compact_spaces(text)
    if not cleaned:
        return []

    parts = re.split(r"[、,/／]| and ", cleaned)
    names = []
    for part in parts:
        name = compact_spaces(part)
        if not name:
            continue
        if name not in names:
            names.append(name)
        if len(names) >= limit:
            break
    return names


def extract_after_label(text: str, labels: list[str], stop_labels: list[str] | None = None) -> str:
    source = sanitize_text(text)
    for label in labels:
        pattern = re.escape(label) + r"\s*(.+)"
        match = re.search(pattern, source, flags=re.IGNORECASE)
        if not match:
            continue

        result = match.group(1)
        if stop_labels:
            stop_pattern = r"\s+(?:" + "|".join(re.escape(label) for label in stop_labels) + r")\s*:?"
            result = re.split(stop_pattern, result, maxsplit=1, flags=re.IGNORECASE)[0]
        return compact_spaces(result)
    return ""


def extract_nightlife_segment(text: str, label_patterns: list[str], stop_patterns: list[str]) -> str:
    source = compact_spaces(text)
    if not source:
        return ""

    label_regex = r"(?:" + "|".join(label_patterns) + r")\s*:?\s*"
    stop_regex = r"(?=" + "|".join(stop_patterns) + r")"
    match = re.search(label_regex + r"(.+?)" + stop_regex, source, flags=re.IGNORECASE)
    if not match:
        match = re.search(label_regex + r"(.+)$", source, flags=re.IGNORECASE)
    if not match:
        return ""

    result = compact_spaces(match.group(1))
    result = re.sub(r"^\[[^\]]+\]\s*", "", result).strip()
    return result


def build_film_highlights(item) -> list[str]:
    highlights = []
    director = sanitize_text(item.get("director", ""))
    cast_names = parse_cast_names(item.get("cast", ""))
    synopsis = film_synopsis_text(item)
    hook = infer_film_hook(synopsis)
    lower = synopsis.lower()

    if director:
        highlights.append(f"With {director} directing, this feels easier to back as a deliberate theatrical pick than a routine release.")
    if cast_names:
        highlights.append(f"The presence of {', '.join(cast_names[:3])} gives the film a stronger audience hook than premise alone.")
    if "海" in synopsis or "space" in lower or "battle" in lower or "monster" in lower:
        highlights.append("The premise sounds built for scale, which makes this the kind of title that should land better in a theater than at home.")
    if "謎" in synopsis or "mystery" in lower or "discover" in lower or "encounter" in lower:
        highlights.append("The mystery engine suggests a plot that keeps unfolding, rather than coasting on spectacle or brand recognition alone.")
    if "friend" in lower or "5人" in synopsis or "team" in lower or "幼馴染" in synopsis:
        highlights.append("Ensemble dynamics look central here, which usually helps a big-concept story stay lively instead of turning schematic.")
    if "technology" in lower or "テクノロジー" in synopsis or "transform" in lower or "beaver" in lower:
        highlights.append("The one-line hook is strong enough to make this feel recommendable on concept, before reviews even enter the picture.")
    if "movie-industry" in hook or "movie" in lower or "映画オタク" in synopsis or "リメイク" in synopsis:
        highlights.append("Its movie-about-movies angle adds a layer of personality that should make it play fresher than a straight genre run-through.")

    return highlights


def build_exhibition_highlights(item) -> list[str]:
    highlights = []
    raw = raw_description_text(item)
    lower = raw.lower()
    title = sanitize_text(item.get("title", "This exhibition"))

    if "video" in lower and "installation" in lower:
        highlights.append("Video and installation work are both central here, so the show reads as spatial as well as image-based")
    elif "video" in lower:
        highlights.append("Moving-image work is central, which changes the pacing from object viewing to time-based attention")
    if "photography" in lower:
        highlights.append("Photography is treated as part of the argument, not just supporting material around the main works")
    if "archival" in lower or "archive" in lower:
        highlights.append("Archival material is used as active evidence, giving the exhibition a stronger research backbone")
    if "fiction and documentary" in lower:
        highlights.append("The tension between fiction and documentary is explicit, which keeps the work from settling into one register")
    if "diaspora" in lower or "diasporic" in lower:
        highlights.append("Diaspora is treated as a lived historical condition, not just an abstract identity theme")
    if "korean diaspora" in lower or "south korea" in lower:
        highlights.append("The Korean diaspora focus gives the research a concrete geopolitical frame instead of a vague transnational one")
    if "migration" in lower or "immigrated" in lower or "foreign lands" in lower:
        highlights.append("Migration is approached through personal memory and movement across borders rather than through policy language alone")
    if "three artists" in lower:
        highlights.append("The three-artist structure keeps the argument comparative, letting different diasporic trajectories sharpen each other")
    if "colonial" in lower or "dictatorship" in lower:
        highlights.append("Colonial history is addressed directly rather than left as distant context behind the work")
    if "borders" in lower or "border" in lower:
        highlights.append("Border-crossing memory is central here, which gives the exhibition a sharper historical and emotional throughline")
    if "climate crisis" in lower or "carbon capture" in lower:
        highlights.append("Climate politics are framed through specific materials and systems instead of broad environmental messaging")
    if any(word in lower for word in ["oil", "tobacco", "sugar", "cotton"]):
        highlights.append("Commodity histories are named directly, which makes the political frame feel materially grounded rather than symbolic")
    if "quantum" in lower:
        highlights.append("Quantum ideas are not background flavor here, but part of the exhibition's actual conceptual structure")
    if "space research" in lower or "space-oriented works" in lower:
        highlights.append("Space research and artist responses are shown side by side, which gives the project a stronger interdisciplinary edge")
    if "japanese quantum computer" in lower:
        highlights.append("Work made with a Japanese quantum computer gives the show a concrete technical hook rather than a vague science-art label")
    if "xr exhibits" in lower:
        highlights.append("XR exhibits shift part of the experience away from static viewing and toward embodied spatial encounter")
    if "talk events" in lower or "dialogues between researchers and artists" in lower:
        highlights.append("Researcher-artist talks extend the exhibition into an active exchange of ideas instead of a closed display")
    if "performance" in lower:
        highlights.append("Performance language shapes the work, which usually makes the exhibition feel more charged than static display")
    if "new works" in lower or "japan premiere" in lower:
        highlights.append(f"{title} includes newly presented material, so it is not just a repeat of already-circulating work")

    return highlights


def looks_like_clean_lineup_segment(text: str, max_words=18) -> bool:
    cleaned = compact_spaces(text)
    if not cleaned:
        return False

    lower = cleaned.lower()
    bad_markers = [
        "open ",
        "door",
        "you must be over",
        "admitted free",
        "photo id",
        "age 20",
        "popup:",
        "food:",
        "photo:",
        "楼",
        "※",
    ]
    if any(marker in lower for marker in bad_markers):
        return False
    if len(cleaned) > 90:
        return False
    if "。" in cleaned or "！" in cleaned or "？" in cleaned:
        return False
    if len(cleaned.split()) > max_words:
        return False
    return True


def build_nightlife_highlights(item) -> list[str]:
    highlights = []
    raw = raw_description_text(item)
    lower = raw.lower()
    title = sanitize_text(item.get("title", "This event"))

    guest_dj = extract_after_label(raw, ["Guest DJ :", "SPECIAL GUEST:", "SPECIAL GUEST DJ:"], ["DJ", "DJ’s", "LIVE", "PHOTO", "FOOD", "Organizer"])
    djs = extract_after_label(raw, ["DJ :", "DJ:", "DJ’s (A to Z) :", "DJ'S (A TO Z) :"], ["LIVE", "PHOTO", "FOOD", "Organizer", "SPECIAL GUEST"])
    live = extract_after_label(raw, ["LIVE :", "LIVE:"], ["PHOTO", "FOOD", "Organizer"])
    organizer = extract_after_label(raw, ["Organizer :", "ORGANIZER :"], ["DJ", "LIVE", "PHOTO", "FOOD"])

    guest_names = split_people(guest_dj, 2)
    dj_names = split_people(djs, 4)
    live_names = split_people(live, 2)

    if guest_names:
        highlights.append(f"Guest names like {', '.join(guest_names)} give the night a sharper draw than a house-party-style weekly")
    if dj_names:
        highlights.append(f"The DJ roster centers on {', '.join(dj_names[:3])}, which helps define the room’s actual character")
    if live_names:
        highlights.append(f"Live appearances from {', '.join(live_names)} make this feel more mixed-format than a straight DJ session")
    if "tour final" in lower or "japan tour" in lower:
        highlights.append("A tour stop or final-date framing raises the sense that this is a one-off booking rather than routine programming")
    if organizer:
        highlights.append(f"Programming by {organizer} suggests a curatorial hand behind the night, not just a loose lineup dump")
    if "azumaya" in title.lower():
        highlights.append("Azumaya’s small-room reputation usually makes lineup details matter more because the crowd stays close to the booth")

    return highlights


def build_activity_highlights(item) -> list[str]:
    highlights = []
    title = sanitize_text(item.get("title", "This event"))
    raw = raw_description_text(item)
    lower = raw.lower()
    title_lower = title.lower()

    if "rose" in title_lower or "rose" in lower:
        highlights.append("The rose focus gives the event a very specific seasonal look rather than a generic spring outing")
    if "shrine" in title_lower or "jingu" in title_lower:
        highlights.append("The shrine setting matters here because ritual atmosphere is part of the experience, not just the backdrop")
    if "garden" in title_lower or "botanical" in lower:
        highlights.append("This works best as a landscape-and-season event, where the setting does as much work as the program")
    if "archery" in title_lower or "yabusame" in title_lower:
        highlights.append("Mounted archery gives the event a strong visual identity that is hard to confuse with a standard local festival")
    if "sumo" in title_lower:
        highlights.append("The baby-sumo format makes this memorable because the spectacle is inseparable from the ritual framing")
    if "oktoberfest" in title_lower:
        highlights.append("The beer-hall format gives this more social energy than a passive sightseeing stop")
    if "333 carp streamers" in title_lower or "koinobori" in title_lower:
        highlights.append("The giant streamer display makes this event legible at a glance, which is exactly why it works as a city-season marker")
    if "award of excellence" in lower:
        highlights.append("The site’s horticultural reputation gives the visit more substance than a simple flower-photo destination")
    if "100th anniversary" in lower:
        highlights.append("An anniversary context adds institutional weight rather than leaving the event as a loose seasonal listing")

    return highlights


def fallback_summary(item) -> str:
    title = item.get("title", "This event")
    category = normalize_category(item.get("category"))
    raw = raw_description_text(item).lower()

    if category == "Film":
        director = sanitize_text(item.get("director", ""))
        hook = infer_film_hook(film_synopsis_text(item))
        if director:
            return f"Directed by {director}, {title} leans on {hook}."
        return f"{title} leans on {hook}."
    if category == "Nightlife":
        return f"{title} is defined by its lineup, timing, and club setting."
    if category == "Activity":
        return f"{title} is a local Tokyo event shaped by timing, place, and public atmosphere."

    if "scale" in raw:
        return f"{title} centers on scale as a way of unsettling perception."
    if "archival" in raw:
        return f"{title} uses archival research and video to connect history with the present."
    if "time" in raw:
        return f"{title} uses time as a framework across multiple artistic practices."
    if "video" in raw:
        return f"{title} presents video-based work shaped by research and performance."

    return f"{title} is defined by a clear structure and a specific point of interest."


def fallback_description(item) -> list[str]:
    raw = raw_description_text(item).lower()
    title = item.get("title", "This event")
    category = normalize_category(item.get("category"))

    if category == "Film":
        synopsis = film_synopsis_text(item)
        director = sanitize_text(item.get("director", ""))
        cast_names = parse_cast_names(item.get("cast", ""))
        cast_text = ", ".join(cast_names[:3])
        hook = infer_film_hook(synopsis)

        first_paragraph = shorten_film_synopsis(synopsis)
        if not first_paragraph:
            first_paragraph = f"{title} is currently in release across selected cinemas in Tokyo."

        second_paragraph = f"What makes it worth a closer look is {hook}."
        if director and cast_text:
            second_paragraph += f" The combination of director {director} and cast members such as {cast_text} gives the film a clearer reason to seek out beyond simple availability."
        elif director:
            second_paragraph += f" Director {director} gives the release a stronger authorial hook than a generic multiplex pick."
        elif cast_text:
            second_paragraph += f" The presence of performers such as {cast_text} gives the project an immediate point of interest."

        return [
            first_paragraph,
            second_paragraph,
        ]

    if category == "Nightlife":
        return [
            f"{title} is shaped by its venue, schedule, and lineup rather than broad nightlife language.",
            "That makes it easier to read as a concrete night out instead of a generic party recommendation."
        ]

    if category == "Activity":
        return [
            f"{title} works as a Tokyo day-out pick with a clear place, date range, and public-facing format.",
            "Its appeal comes from local atmosphere and timing, which makes it easy to fit into a broader city plan."
        ]

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
        f"{title} presents a clearly framed event with a distinct structure or subject.",
        "The presentation emphasizes the details that separate it from a generic listing."
    ]


def fallback_highlights(item) -> list[str]:
    raw = raw_description_text(item).lower()
    category = normalize_category(item.get("category"))
    title = sanitize_text(item.get("title", "This event"))
    venue = sanitize_text(item.get("venue", "the venue"))
    area = sanitize_text(item.get("area", "Tokyo"))
    highlights = []

    if category == "Film":
        director = sanitize_text(item.get("director", ""))
        cast_names = parse_cast_names(item.get("cast", ""))
        synopsis = film_synopsis_text(item)
        hook = infer_film_hook(synopsis)

        if director:
            highlights.append(f"Directed by {director}, which gives the release a clearer authorial identity than a generic studio listing")
        if cast_names:
            highlights.append(f"Cast members such as {', '.join(cast_names[:3])} give the film immediate viewer-facing appeal")
        if synopsis:
            highlights.append(f"The setup suggests {hook}, making it easier to recommend without leaning on spoilers")
        if "海" in synopsis or "space" in synopsis.lower() or "battle" in synopsis.lower():
            highlights.append("The premise looks built for scale, which matters more when you are choosing a theatrical watch")
        if "謎" in synopsis or "mystery" in synopsis.lower():
            highlights.append("A mystery element gives the story narrative pull beyond pure spectacle or franchise familiarity")
        if "リメイク" in synopsis or "movie" in synopsis.lower() or "映画オタク" in synopsis:
            highlights.append("A movie-about-movies angle gives the material personality beyond a straightforward genre setup")

    if category == "Nightlife":
        if "dj" in raw or "line up" in raw or "lineup" in raw:
            highlights.append("Lineup detail is central to the event's appeal")
        if "club" in raw or "venue" in raw:
            highlights.append("Venue identity is a meaningful part of the night rather than background information")
        if "open:" in raw or "22:00" in raw:
            highlights.append("Late-night scheduling signals a dedicated club format")

    if category == "Activity":
        if "festival" in raw or "market" in raw:
            highlights.append("Public event format makes it easy to visit without specialist planning")
        if "season" in raw or "spring" in raw or "cherry blossom" in raw:
            highlights.append("Seasonal timing is part of the event's appeal")
        if "tokyo" in raw:
            highlights.append("The listing is grounded in a specific Tokyo neighborhood or destination")

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

    if category == "Exhibition":
        fallback_pool = [
            f"{title} is best approached as a focused stop rather than a quick photo-only visit.",
            f"The venue context at {venue} adds useful framing before you see the work itself.",
            "This is a strong pick if you want one clearly defined exhibition rather than a large mixed program.",
            "Give yourself enough time to read the wall text and let the structure of the show come through."
        ]
    elif category == "Film":
        fallback_pool = [
            f"{title} is easier to recommend when the premise matters as much as simple availability.",
            "The combination of cast, director, and story hook gives it more shape than a generic listing.",
            "This feels closer to a movie you choose for its angle than one you watch only because it is nearby.",
            "The linked cinema list makes it easy to turn interest into an actual screening plan."
        ]
    elif category == "Nightlife":
        fallback_pool = [
            f"{title} is worth considering if venue identity matters as much as the lineup.",
            f"It is a stronger choice for a dedicated night out in {area} than a casual bar-hopping plan.",
            "Arriving earlier usually makes it easier to settle in before the room gets fully busy.",
            "This is the kind of listing where checking the lineup and set times in advance really helps."
        ]
    else:
        fallback_pool = [
            f"{title} works well if you want a public-facing event that is easy to fit into a Tokyo itinerary.",
            f"It is especially useful as a daytime pick around {area} rather than a destination that needs heavy planning.",
            "This kind of event is usually best paired with a nearby museum, garden, or neighborhood walk.",
            "Checking weather and official timing before you go will make the visit smoother."
        ]

    if category == "Film" and len(deduped) >= 3:
        return deduped[:4]

    for line in fallback_pool:
        if line not in deduped:
            deduped.append(line)
        if len(deduped) >= 4:
            break

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


def build_exhibition_highlights(item) -> list[str]:
    highlights = []
    raw = raw_description_text(item)
    lower = raw.lower()
    title = sanitize_text(item.get("title", "This exhibition"))

    if "video" in lower and "installation" in lower:
        highlights.append("Video and installation work are both central here, so the show reads as spatial as well as image-based")
    elif "video" in lower:
        highlights.append("Moving-image work is central, which changes the pacing from object viewing to time-based attention")
    if "photography" in lower:
        highlights.append("Photography is treated as part of the argument, not just supporting material around the main works")
    if "archival" in lower or "archive" in lower:
        highlights.append("Archival material is used as active evidence, giving the exhibition a stronger research backbone")
    if "fiction and documentary" in lower:
        highlights.append("The tension between fiction and documentary is explicit, which keeps the work from settling into one register")
    if "diaspora" in lower or "diasporic" in lower:
        highlights.append("Diaspora is treated as a lived historical condition, not just an abstract identity theme")
    if "korean diaspora" in lower or "south korea" in lower:
        highlights.append("The Korean diaspora focus gives the research a concrete geopolitical frame instead of a vague transnational one")
    if "migration" in lower or "immigrated" in lower or "foreign lands" in lower:
        highlights.append("Migration is approached through personal memory and movement across borders rather than through policy language alone")
    if "three artists" in lower:
        highlights.append("The three-artist structure keeps the argument comparative, letting different diasporic trajectories sharpen each other")
    if "colonial" in lower or "dictatorship" in lower:
        highlights.append("Colonial history is addressed directly rather than left as distant context behind the work")
    if "borders" in lower or "border" in lower:
        highlights.append("Border-crossing memory is central here, which gives the exhibition a sharper historical and emotional throughline")
    if "climate crisis" in lower or "carbon capture" in lower:
        highlights.append("Climate politics are framed through specific materials and systems instead of broad environmental messaging")
    if any(word in lower for word in ["oil", "tobacco", "sugar", "cotton"]):
        highlights.append("Commodity histories are named directly, which makes the political frame feel materially grounded rather than symbolic")
    if "performance" in lower:
        highlights.append("Performance language shapes the work, which usually makes the exhibition feel more charged than static display")
    if "new works" in lower or "japan premiere" in lower:
        highlights.append(f"{title} includes newly presented material, so it is not just a repeat of already-circulating work")

    return highlights


def build_nightlife_highlights(item) -> list[str]:
    highlights = []
    raw = raw_description_text(item)
    lower = raw.lower()
    title = sanitize_text(item.get("title", "This event"))

    stop_patterns = [
        r"SPECIAL\s+GUEST(?:\s+DJ)?\s*:",
        r"GUEST\s+DJ\s*:",
        r"DJ(?:'S|’S|鈥檚)?(?:\s*\(A\s*TO\s*Z\))?\s*:",
        r"LIVE\s*:",
        r"PHOTO\s*:",
        r"FOOD\s*:",
        r"ORGANIZER\s*:",
        r"\[[^\]]+\]\s+\w+\s+DJ\s*:",
    ]
    guest_dj = extract_nightlife_segment(raw, [r"GUEST\s+DJ", r"SPECIAL\s+GUEST(?:\s+DJ)?"], stop_patterns)
    djs = extract_nightlife_segment(raw, [r"DJ(?:'S|’S|鈥檚)?(?:\s*\(A\s*TO\s*Z\))?"], stop_patterns)
    live = extract_nightlife_segment(raw, [r"LIVE"], stop_patterns)
    organizer = extract_nightlife_segment(raw, [r"ORGANIZER"], stop_patterns)

    if not looks_like_clean_lineup_segment(guest_dj, 8):
        guest_dj = ""
    if not looks_like_clean_lineup_segment(djs, 18):
        djs = ""
    if not looks_like_clean_lineup_segment(live, 10):
        live = ""
    if not looks_like_clean_lineup_segment(organizer, 5):
        organizer = ""

    guest_names = split_people(guest_dj, 2)
    dj_names = split_people(djs, 4)
    live_names = split_people(live, 2)

    if guest_names:
        highlights.append(f"Guest names like {', '.join(guest_names)} give the night a sharper draw than a house-party-style weekly")
    if dj_names:
        highlights.append(f"The core DJ roster around {', '.join(dj_names[:3])} gives the night a more legible musical identity")
    if live_names:
        highlights.append(f"Live appearances from {', '.join(live_names)} make this feel more mixed-format than a straight DJ session")
    if "tour final" in lower or "japan tour" in lower:
        highlights.append("A tour stop or final-date framing raises the sense that this is a one-off booking rather than routine programming")
    if organizer:
        highlights.append(f"Programming by {organizer} suggests a curatorial hand behind the night, not just a loose lineup dump")
    genre_hits = []
    for genre in ["afro", "house", "techno", "bass", "hip hop", "reggae"]:
        if genre in lower and genre not in genre_hits:
            genre_hits.append(genre)
    if genre_hits:
        highlights.append(f"Genre cues like {', '.join(genre_hits[:2])} make the floor direction easier to picture before you even arrive")
    if "azumaya" in title.lower():
        highlights.append("Azumaya’s small-room reputation usually makes lineup details matter more because the crowd stays close to the booth")

    return highlights


def build_activity_highlights(item) -> list[str]:
    highlights = []
    title = sanitize_text(item.get("title", "This event"))
    raw = raw_description_text(item)
    lower = raw.lower()
    title_lower = title.lower()

    if "rose" in title_lower or "rose" in lower:
        highlights.append("The rose focus gives the event a very specific seasonal look rather than a generic spring outing")
    if "grand festival" in title_lower:
        highlights.append("A grand-festival framing usually means formal processions, shrine ritual, and stage programs rather than a simple fairground feel")
    if "shrine" in title_lower or "jingu" in title_lower:
        highlights.append("The shrine setting matters here because ritual atmosphere is part of the experience, not just the backdrop")
    if "garden" in title_lower or "botanical" in lower:
        highlights.append("This works best as a landscape-and-season event, where the setting does as much work as the program")
    if "azalea" in title_lower or "azaleas" in title_lower:
        highlights.append("The azalea focus makes the garden read in broad color fields, which is different from single-specimen flower viewing")
    if "peony" in title_lower or "peonies" in title_lower:
        highlights.append("The peony angle matters because it gives the visit a dense, ornamental spring focus rather than a broad flower mix")
    if "sakura" in title_lower or "blossom" in title_lower:
        highlights.append("Cherry-blossom framing makes timing unusually important here, since the appeal depends on catching a short-lived peak")
    if "archery" in title_lower or "yabusame" in title_lower:
        highlights.append("Mounted archery gives the event a strong visual identity that is hard to confuse with a standard local festival")
    if "regatta" in title_lower or "boat race" in title_lower:
        highlights.append("A regatta format changes the energy from passive sightseeing to spectatorship built around motion and rivalry")
    if "sumo" in title_lower:
        highlights.append("The baby-sumo format makes this memorable because the spectacle is inseparable from the ritual framing")
    if "oktoberfest" in title_lower:
        highlights.append("The beer-hall format gives this more social energy than a passive sightseeing stop")
    if "earth day" in title_lower:
        highlights.append("Earth Day framing usually brings workshops and public participation, which makes the event more active than a standard fair")
    if "street stage" in title_lower:
        highlights.append("A street-stage setup keeps the event open and kinetic, with performance acting as the main draw rather than background entertainment")
    if "darkness festival" in title_lower:
        highlights.append("The darkness-festival identity already carries a dramatic mood, so the appeal is closer to spectacle and ritual than daytime browsing")
    if "333 carp streamers" in title_lower or "koinobori" in title_lower:
        highlights.append("The giant streamer display makes this event legible at a glance, which is exactly why it works as a city-season marker")
    if "award of excellence" in lower:
        highlights.append("The site’s horticultural reputation gives the visit more substance than a simple flower-photo destination")
    if "100th anniversary" in lower:
        highlights.append("An anniversary context adds institutional weight rather than leaving the event as a loose seasonal listing")

    return highlights


def fallback_highlights(item) -> list[str]:
    category = normalize_category(item.get("category"))
    title = sanitize_text(item.get("title", "This event"))
    venue = sanitize_text(item.get("venue", "the venue"))
    area = sanitize_text(item.get("area", "Tokyo"))
    date_text = sanitize_text(item.get("date", ""))
    price = sanitize_text(item.get("price", ""))
    raw = raw_description_text(item).lower()

    if category == "Film":
        highlights = build_film_highlights(item)
        fallback_pool = [
            f"{title} needs a concrete reason to watch beyond simple release-week visibility.",
            "The recommendation should stand on the director, cast, or premise rather than generic availability.",
            "A strong movie pick still needs a clear hook even before you look at showtimes.",
            "If the film has no distinct angle, it should not read like a strong recommendation."
        ]
    elif category == "Nightlife":
        highlights = build_nightlife_highlights(item)
        fallback_pool = [
            f"{title} only becomes compelling once the actual DJs, guests, or room identity are made concrete.",
            f"A useful nightlife recommendation in {area} should tell you who is shaping the floor and why.",
            "The more specific the lineup details are, the easier it is to picture the night’s real atmosphere.",
            "If a nightlife highlight could fit any club, it is not strong enough."
        ]
    elif category == "Activity":
        highlights = build_activity_highlights(item)
        fallback_pool = [
            f"{title} should only survive if it has one memorable trait people can repeat back in a sentence.",
            f"A strong activity listing around {area} needs a specific ritual, seasonal feature, or public format that stands out.",
            "The interesting part should come from what actually happens there, not just from where it is.",
            "If the same highlight could fit ten other outings, it is too weak."
        ]
    else:
        highlights = build_exhibition_highlights(item)
        fallback_pool = [
            f"{title} is only worth recommending if the medium, subject, or research method is doing something specific.",
            f"The framing at {venue} matters because this appears built around a clear argument rather than a loose survey.",
            "A strong exhibition highlight should tell you what kind of work is actually carrying the show.",
            "If the exhibition has no concrete material or thematic hook, it should not survive as a featured listing."
        ]

    deduped = []
    for line in highlights:
        line = sanitize_text(line)
        if line and line not in deduped:
            deduped.append(line)

    if deduped:
        return deduped[:4]

    if category == "Nightlife":
        if venue:
            deduped.append(f"At {venue}, this reads more like a room-led club pick than a big headline-driven booking.")
        if re.search(r"\b(21|22|23):\d{2}\b", date_text):
            deduped.append("The late start points to a full-night floor session, so it suits people choosing one room and settling in.")
        elif price and ("before 23:00" in price.lower() or "u-23" in price.lower()):
            deduped.append("Early-entry and U-23 pricing suggest a local regulars' night rather than a one-off spectacle booking.")
        if price and ("before 23:00" in price.lower() or "u-23" in price.lower()):
            deduped.append("The entry structure rewards arriving early, which usually means the night is built to develop over hours rather than peak instantly.")
    elif category == "Exhibition":
        lower_title = title.lower()
        if "quantum" in lower_title or "space" in lower_title:
            deduped.append("The science-art framing gives the exhibition a clearer conceptual angle than a broad contemporary group show.")
        if "mission" in lower_title or "art" in lower_title:
            deduped.append("Its appeal depends on how artistic expression is pushed toward research territory rather than staying in a purely visual register.")
        if not deduped and venue:
            deduped.append(f"The project at {venue} reads more like a framed proposition than a loose survey, which helps it stand out.")
    elif category == "Activity":
        if venue and area:
            deduped.append(f"The event's appeal is tied to its specific setting around {area}, not just to a generic seasonal label.")
        elif venue:
            deduped.append(f"The setting at {venue} is doing real work here, so this is more place-specific than a generic city listing.")
    elif category == "Film":
        if title:
            deduped.append(f"{title} still needs a concrete hook from its premise, cast, or director to justify the recommendation.")
        if date_text:
            deduped.append("The main value here is that it is a current theatrical option in Tokyo rather than a catalog title to save for later.")

    return deduped[:2]


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
        print(f"[WARN] Unsupported detail detected: {item.get('title')} -> {suspicious_terms}")

    return len(suspicious_terms) > 0


def parse_ai_json(content: str):
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```json\s*|^```\s*|```$", "", content, flags=re.MULTILINE).strip()
    return json.loads(content)


def generate_ai_content(client: OpenAI, item):
    if client is None:
        return {
            "summary": fallback_summary(item),
            "description": fallback_description(item),
            "highlights": fallback_highlights(item),
            "_status": "fallback",
        }

    prompt = sanitize_text(build_prompt(item))
    model_name = "gpt-4o" if is_high_priority(item) else "gpt-4o-mini"

    messages = [
        {
            "role": "system",
            "content": (
                "You are the lead editor of a Tokyo culture guide. "
                "Write with editorial judgment and specificity. "
                "Avoid brochure language, generic praise, logistics-heavy phrasing, neutral database summaries, "
                "and invented evaluative claims such as breathtaking visuals, stellar casts, or unforgettable atmosphere "
                "unless the source explicitly supports them. "
                "Return strict JSON only."
            ),
        },
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
                  "temperature": 0.0,
              }
          )
    except Exception as e:
        print(f"[ERROR] Local JSON check failed for: {item.get('title')}")
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
            temperature=0.0,
        )
    except Exception as e:
        print(f"[ERROR] API request failed for: {item.get('title')}")
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
                temperature=0.0,
            )
        except Exception as e2:
            print(f"[ERROR] Retry API request failed for: {item.get('title')}")
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
        print("[ERROR] JSON parse failed for:", item.get("title"))
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
          "unforgettable",
          "breathtaking",
          "must-see",
          "stellar cast",
          "vibrant",
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
    attempts = HIGH_PRIORITY_AI_ATTEMPTS if is_high_priority(item) else NORMAL_AI_ATTEMPTS
    print(f"[GEN] Generating: {title} | attempts={attempts}")

    candidates = []

    for _ in range(attempts):
        ai = generate_ai_content(client, item)
        candidates.append(ai)

    best_ai, best_quality = pick_best_result(candidates, item)

    if not best_quality["publishable"]:
        print(
            f"[WARN] Not publishable yet: {title} | "
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
        "director": item.get("director", ""),
        "cast": item.get("cast", ""),
        "screeningVenues": item.get("screeningVenues", []),
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

        client = get_client() if os.environ.get("OPENAI_API_KEY") else None
        if client is None:
            print("OPENAI_API_KEY not found, using fallback event copy generation.")
        raw_events = load_raw_events()
        total_events = len(raw_events)
        print(
            f"[INFO] Loaded {total_events} raw events | "
            f"normal_attempts={NORMAL_AI_ATTEMPTS} "
            f"high_priority_attempts={HIGH_PRIORITY_AI_ATTEMPTS}"
        )

        final_events = []
        for i, item in enumerate(raw_events):
            try:
                validate_event(item)
                print(
                    f"[PROGRESS] {i + 1}/{total_events} | "
                    f"{item.get('category', 'Unknown')} | {item.get('title', 'Unknown')}"
                )
                enriched = enrich_event(client, item, i)
                final_events.append(enriched)
            except Exception as e:
                print(f"[WARN] Failed to enrich event {item.get('title', 'Unknown')}: {e}")
                continue

        final_events = dedupe_events(final_events)

        valid_events = []
        for event in final_events:
            try:
                validate_final_event_schema(event)
                valid_events.append(event)
            except ValueError as e:
                print(f"[WARN] Skipping invalid event {event.get('title', 'Unknown')}: {e}")

        final_events = valid_events

        save_events(final_events)
        print(f"\n[DONE] Generated {len(final_events)} deduped events -> {OUTPUT_PATH}")

    finally:
        cleanup_build_lock()


if __name__ == "__main__":
    main()
