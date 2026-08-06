from datetime import date, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from db import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/habits", tags=["habits"])


class HabitLogRequest(BaseModel):
    log_date: Optional[str] = None
    water_l: float = 0
    sleep_hours: float = 0
    workout_done: bool = False
    steps: int = 0
    calories_consumed: float = 0
    calories_burned: float = 0
    protein_g: float = 0
    mood: Optional[str] = None
    energy_level: Optional[int] = None
    stress_level: Optional[int] = None
    weight_kg: Optional[float] = None
    waist_cm: Optional[float] = None


@router.post("")
def log_habit(body: HabitLogRequest, user=Depends(get_current_user), db=Depends(get_db)):
    log_date = body.log_date or date.today().isoformat()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO habit_logs (user_id, log_date, water_l, sleep_hours, workout_done, steps,
                calories_consumed, calories_burned, protein_g, mood, energy_level, stress_level, weight_kg, waist_cm)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (user_id, log_date) DO UPDATE SET
                water_l=excluded.water_l, sleep_hours=excluded.sleep_hours, workout_done=excluded.workout_done,
                steps=excluded.steps, calories_consumed=excluded.calories_consumed,
                calories_burned=excluded.calories_burned, protein_g=excluded.protein_g, mood=excluded.mood,
                energy_level=excluded.energy_level, stress_level=excluded.stress_level,
                weight_kg=excluded.weight_kg, waist_cm=excluded.waist_cm
            RETURNING *
        """, (user["id"], log_date, body.water_l, body.sleep_hours, body.workout_done, body.steps,
              body.calories_consumed, body.calories_burned, body.protein_g, body.mood,
              body.energy_level, body.stress_level, body.weight_kg, body.waist_cm))
        return cur.fetchone()


@router.get("")
def list_habits(days: int = 30, user=Depends(get_current_user), db=Depends(get_db)):
    cutoff = date.today() - timedelta(days=min(days, 365))
    with db.cursor() as cur:
        cur.execute("SELECT * FROM habit_logs WHERE user_id = %s AND log_date >= %s ORDER BY log_date",
                     (user["id"], cutoff))
        return cur.fetchall()

@router.get("/streak")
def get_workout_streak(user=Depends(get_current_user), db=Depends(get_db)):
    """Calculates the current consecutive workout streak for the user."""
    uid = user["id"]
    with db.cursor() as cur:
        # Fetch all dates where workout was done, ordered by newest first
        cur.execute("""
            SELECT log_date 
            FROM habit_logs 
            WHERE user_id = %s AND workout_done = TRUE 
            ORDER BY log_date DESC
        """, (uid,))
        rows = cur.fetchall()
    
    if not rows:
        return {"current_streak": 0}

    # Extract dates into a set for fast lookup
    # Depending on your database cursor implementation, rows might be dicts or tuples.
    # Assuming standard dictionary or tuple where log_date is index 0 or 'log_date':
    logged_dates = {str(row["log_date"] if isinstance(row, dict) else row[0]) for row in rows}

    streak = 0
    check_date = date.today()
    
    # If today's workout isn't logged/done yet, check if yesterday extends the streak
    today_str = check_date.isoformat()
    if today_str not in logged_dates:
        check_date -= timedelta(days=1)
        
    # Count backwards consecutively
    while True:
        date_str = check_date.isoformat()
        if date_str in logged_dates:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break

    return {"current_streak": streak}