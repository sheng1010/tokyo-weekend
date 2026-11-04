# Tokyo Weekend

Static guide to films, exhibitions, nightlife, and activities in Tokyo. Listings with an end date in the past are hidden. Films that only say “now showing”, with no end date, are not presented as current.

Live site: https://tokyo-weekend.vercel.app

## Run locally

```bash
python3 -m http.server 8000
```

Open http://127.0.0.1:8000/. On localhost, event links use `event.html?slug=...`. Production rewrites `/event/:slug` via `vercel.json`.

## Data pipeline

Scrapers live in `sources/`. `main.py` writes `data/raw_events.json` (gitignored). `build_events.py` writes `data/generated_events.json`.

Editorial copy uses the OpenAI API when `OPENAI_API_KEY` is set in the environment. Do not commit that key. Without it, the build uses the fallback copy in `build_events.py`.

```bash
pip install -r requirements.txt
python main.py
```

Exhibition records keep a `popularityScore` from `utils/score_utils.py`.

## Sitemap

```bash
python generate_sitemap.py
```

This rewrites `sitemap.xml` from the current event file and today’s date.

## Contact

miza12211@gmail.com
