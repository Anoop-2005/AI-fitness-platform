import httpx

WGER_BASE_URL = "https://wger.de/api/v2"
ENGLISH_LANGUAGE_ID = 2


def fetch_exercises_page(limit: int = 50, offset: int = 0) -> dict:
    """One page of wger's exerciseinfo endpoint (full details, not just IDs)."""
    resp = httpx.get(
        f"{WGER_BASE_URL}/exerciseinfo/",
        params={"limit": limit, "offset": offset, "language": ENGLISH_LANGUAGE_ID, "format": "json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def parse_exercise(raw: dict) -> dict | None:
    """
    Turns one wger exerciseinfo result into the shape our exercises_cache
    table expects. Returns None if there's no English translation to use
    (some entries are translation-only in other languages).
    """
    translations = raw.get("translations", [])
    english = next((t for t in translations if t.get("language") == ENGLISH_LANGUAGE_ID), None)
    if not english or not english.get("name"):
        return None

    images = raw.get("images", [])
    image_url = images[0]["image"] if images else None

    return {
        "wger_id": raw["id"],
        "name": english["name"],
        "muscle_group": (raw.get("category") or {}).get("name"),
        "secondary_muscles": [m.get("name_en") or m.get("name") for m in raw.get("muscles_secondary", [])],
        "equipment": [e.get("name") for e in raw.get("equipment", [])],
        "difficulty": None,  # wger doesn't provide this; left for manual curation later if wanted
        "instructions": english.get("description", ""),
        "image_url": image_url,
    }


def fetch_and_parse_all(max_pages: int = 3, page_size: int = 50) -> list[dict]:
    """
    Fetches a bounded number of pages (not the entire wger database — see
    DESIGN.md's note on syncing a curated subset rather than everything).
    """
    results = []
    offset = 0
    for _ in range(max_pages):
        page = fetch_exercises_page(limit=page_size, offset=offset)
        for raw in page.get("results", []):
            parsed = parse_exercise(raw)
            if parsed:
                results.append(parsed)
        if not page.get("next"):
            break
        offset += page_size
    return results
