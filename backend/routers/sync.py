"""
These endpoints populate the shared exercises_cache/foods_cache tables.
They're not user actions — you (the developer) call them once to seed data,
or put them behind a cron job. Protected by a simple shared secret instead
of user login, since no regular user should ever call these.
"""
from fastapi import APIRouter, Depends, HTTPException, Header

from db import get_db
from config import SYNC_SECRET
from services import wger_client, usda_client

router = APIRouter(prefix="/api/sync", tags=["sync"])


def require_sync_secret(x_sync_secret: str | None = Header(default=None)):
    if x_sync_secret != SYNC_SECRET:
        raise HTTPException(status_code=403, detail="Invalid sync secret")


@router.post("/exercises", dependencies=[Depends(require_sync_secret)])
def sync_exercises(db=Depends(get_db), max_pages: int = 3):
    exercises = wger_client.fetch_and_parse_all(max_pages=max_pages)
    with db.cursor() as cur:
        for ex in exercises:
            cur.execute("""
                INSERT INTO exercises_cache (wger_id, name, muscle_group, secondary_muscles, equipment,
                    difficulty, instructions, image_url, synced_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s, now())
                ON CONFLICT (wger_id) DO UPDATE SET
                    name=excluded.name, muscle_group=excluded.muscle_group,
                    secondary_muscles=excluded.secondary_muscles, equipment=excluded.equipment,
                    instructions=excluded.instructions, image_url=excluded.image_url, synced_at=now()
            """, (ex["wger_id"], ex["name"], ex["muscle_group"], __import__("json").dumps(ex["secondary_muscles"]),
                  __import__("json").dumps(ex["equipment"]), ex["difficulty"], ex["instructions"], ex["image_url"]))
    return {"synced": len(exercises)}


@router.post("/foods", dependencies=[Depends(require_sync_secret)])
def sync_foods(query: str, db=Depends(get_db), page_size: int = 20):
    foods = usda_client.search_foods(query, page_size=page_size)
    with db.cursor() as cur:
        for f in foods:
            cur.execute("""
                INSERT INTO foods_cache (fdc_id, name, calories, protein_g, carbs_g, fat_g, fiber_g, serving_size, synced_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s, now())
                ON CONFLICT (fdc_id) DO UPDATE SET
                    name=excluded.name, calories=excluded.calories, protein_g=excluded.protein_g,
                    carbs_g=excluded.carbs_g, fat_g=excluded.fat_g, fiber_g=excluded.fiber_g,
                    serving_size=excluded.serving_size, synced_at=now()
            """, (f["fdc_id"], f["name"], f["calories"], f["protein_g"], f["carbs_g"], f["fat_g"],
                  f["fiber_g"], f["serving_size"]))
    return {"synced": len(foods)}
