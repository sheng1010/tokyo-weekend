import json

EVENTS_PATH = "data/events.json"
GENERATED_PATH = "data/generated_events.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def is_valid_text(value):
    return isinstance(value, str) and value.strip() != ""


def is_valid_description(value):
    return isinstance(value, list) and len(value) > 0 and any(
        isinstance(x, str) and x.strip() for x in value
    )


def is_valid_highlights(value):
    return isinstance(value, list) and len(value) > 0 and any(
        isinstance(x, str) and x.strip() for x in value
    )


def build_index(events):
    by_slug = {}
    by_title = {}

    for event in events:
        slug = (event.get("slug") or "").strip()
        title = (event.get("title") or "").strip()

        if slug:
            by_slug[slug] = event
        if title:
            by_title[title] = event

    return by_slug, by_title


def merge():
    events = load_json(EVENTS_PATH)
    generated = load_json(GENERATED_PATH)

    by_slug, by_title = build_index(events)

    merged_count = 0
    skipped_count = 0

    for gen in generated:
        slug = (gen.get("slug") or "").strip()
        title = (gen.get("title") or "").strip()

        target = None
        if slug and slug in by_slug:
            target = by_slug[slug]
        elif title and title in by_title:
            target = by_title[title]

        if not target:
            print(f"⚠️ No match found: {title or slug}")
            skipped_count += 1
            continue

        changed = False

        if is_valid_text(gen.get("summary")):
            target["summary"] = gen["summary"].strip()
            changed = True

        if is_valid_description(gen.get("description")):
            target["description"] = [x.strip() for x in gen["description"] if isinstance(x, str) and x.strip()]
            changed = True

        if is_valid_highlights(gen.get("highlights")):
            target["highlights"] = [x.strip() for x in gen["highlights"] if isinstance(x, str) and x.strip()]
            changed = True

        if changed:
            merged_count += 1
            print(f"✅ Merged: {target.get('title', '(untitled)')}")
        else:
            skipped_count += 1
            print(f"⚠️ Nothing merged: {title or slug}")

    save_json(EVENTS_PATH, events)
    print(f"\n🎉 Done! merged={merged_count}, skipped={skipped_count}")


if __name__ == "__main__":
    merge()