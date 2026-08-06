'''
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
import json
from db import get_db
from auth import get_current_user
from agents.workout_planner import generate_workout_plan
from agents.diet_planner import generate_diet_plan
from agents.review_agent import generate_weekly_review, aggregate_week

router = APIRouter(prefix="/api", tags=["plans"])


def _get_profile(db, user_id):
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.user_id, p.height_cm, p.current_weight_kg, p.target_weight_kg, p.age, p.gender,
                   p.activity_level, h.knee_problems, h.back_pain, h.joint_pain,
                   f.primary_goal, f.experience_level, f.gym_availability, f.equipment_available, f.days_per_week,
                   d.diet_type, d.food_allergies, d.meals_per_day
            FROM profiles p
            LEFT JOIN health_assessments h ON h.user_id = p.user_id
            LEFT JOIN fitness_prefs f ON f.user_id = p.user_id
            LEFT JOIN diet_prefs d ON d.user_id = p.user_id
            WHERE p.user_id = %s
        """, (user_id,))
        return cur.fetchone()
def _get_profile(db, user_id):
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.user_id, p.height_cm, p.current_weight_kg, p.target_weight_kg, p.age, p.gender,
                   p.activity_level, h.knee_problems, h.back_pain, h.joint_pain,
                   f.primary_goal, f.experience_level, f.gym_availability, f.equipment_available, 
                   COALESCE(f.days_per_week, 7) AS days_per_week,
                   d.diet_type, d.food_allergies, 
                   COALESCE(d.meals_per_day, 8) AS meals_per_day
            FROM profiles p
            LEFT JOIN health_assessments h ON h.user_id = p.user_id
            LEFT JOIN fitness_prefs f ON f.user_id = p.user_id
            LEFT JOIN diet_prefs d ON d.user_id = p.user_id
            WHERE p.user_id = %s
        """, (user_id,))
        profile = cur.fetchone()
        
        # Absolute safeguard fallback if profile row itself is sparse
        if profile:
            profile["days_per_week"] = int(profile.get("days_per_week") or 7)
            profile["meals_per_day"] = int(profile.get("meals_per_day") or 8)
            
        return profile

def _get_latest_analysis(db, user_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM body_analysis WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        return cur.fetchone()


def _get_latest_review(db, user_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM weekly_reviews WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        return cur.fetchone()


@router.get("/review/weekly")
def weekly_review(user=Depends(get_current_user), db=Depends(get_db)):
    cutoff = date.today() - timedelta(days=7)
    with db.cursor() as cur:
        cur.execute("SELECT * FROM habit_logs WHERE user_id = %s AND log_date >= %s ORDER BY log_date",
                     (user["id"], cutoff))
        logs = cur.fetchall()

    review = generate_weekly_review(logs)
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO weekly_reviews (user_id, week_start, stats, plateau_detected, summary)
            VALUES (%s,%s,%s,%s,%s) RETURNING id
        """, (user["id"], cutoff, __import__("json").dumps(review["stats"]), review["plateau_detected"], review["summary"]))
        review["id"] = cur.fetchone()["id"]
    return review
@router.get("/review/weekly")
def weekly_review(user=Depends(get_current_user), db=Depends(get_db)):
    uid = user["id"]
    today = date.today()
    week_start = today - timedelta(days=6)  # Covers exactly 7 days including today

    with db.cursor() as cur:
        # Check if a review for this week window already exists
        cur.execute("""
            SELECT * FROM weekly_reviews 
            WHERE user_id = %s AND week_start = %s 
            ORDER BY id DESC LIMIT 1
        """, (uid, week_start))
        existing_review = cur.fetchone()

        if existing_review:
            return existing_review

        # Fetch habit logs ensuring inclusive range up to today
        cur.execute("""
            SELECT * FROM habit_logs 
            WHERE user_id = %s AND log_date >= %s AND log_date <= %s
            ORDER BY log_date
        """, (uid, week_start, today))
        logs = cur.fetchall()

    # Generate review stats and summary using your agent workflow
    review = generate_weekly_review(logs)

    # Save and return the review
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO weekly_reviews (user_id, week_start, stats, plateau_detected, summary)
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING id, user_id, week_start, stats, plateau_detected, summary, created_at
        """, (
            uid, 
            week_start, 
            json.dumps(review["stats"]), 
            review["plateau_detected"], 
            review["summary"]
        ))
        saved_row = cur.fetchone()

    return saved_row


@router.post("/plans/workout")
def create_workout_plan(user=Depends(get_current_user), db=Depends(get_db)):
    profile = _get_profile(db, user["id"])
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    review = _get_latest_review(db, user["id"])

    rows = generate_workout_plan(db, profile, review)
    if not rows:
        raise HTTPException(status_code=422, detail="No matching exercises found — try syncing exercises first (POST /api/sync/exercises)")

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO workout_plans (user_id, week_start, based_on_review_id) VALUES (%s,%s,%s) RETURNING id
        """, (user["id"], date.today(), review["id"] if review else None))
        plan_id = cur.fetchone()["id"]
        for r in rows:
            cur.execute("""
                INSERT INTO workout_plan_exercises (workout_plan_id, wger_id, day_number, sets, reps, rest_seconds, order_in_day)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (plan_id, r["wger_id"], r["day_number"], r["sets"], r["reps"], r["rest_seconds"], r["order_in_day"]))

    return _fetch_workout_plan(db, plan_id)


@router.get("/plans/workout/latest")
def latest_workout_plan(user=Depends(get_current_user), db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT id FROM workout_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No workout plan yet")
    return _fetch_workout_plan(db, row["id"])


def _fetch_workout_plan(db, plan_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM workout_plans WHERE id = %s", (plan_id,))
        plan = cur.fetchone()
        cur.execute("""
            SELECT wpe.*, ec.name, ec.muscle_group, ec.instructions, ec.image_url
            FROM workout_plan_exercises wpe
            JOIN exercises_cache ec ON ec.wger_id = wpe.wger_id
            WHERE wpe.workout_plan_id = %s
            ORDER BY wpe.day_number, wpe.order_in_day
        """, (plan_id,))
        exercises = cur.fetchall()

    days = {}
    for ex in exercises:
        days.setdefault(ex["day_number"], []).append(ex)
    return {**plan, "days": [{"day_number": d, "exercises": ex} for d, ex in sorted(days.items())]}


@router.post("/plans/diet")
def create_diet_plan(user=Depends(get_current_user), db=Depends(get_db)):
    profile = _get_profile(db, user["id"])
    analysis = _get_latest_analysis(db, user["id"])
    if not profile or not analysis:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    review = _get_latest_review(db, user["id"])

    rows = generate_diet_plan(db, profile, analysis, review)
    if not rows:
        raise HTTPException(status_code=422, detail="No matching foods found — try syncing foods first (POST /api/sync/foods)")

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO diet_plans (user_id, week_start, based_on_review_id) VALUES (%s,%s,%s) RETURNING id
        """, (user["id"], date.today(), review["id"] if review else None))
        plan_id = cur.fetchone()["id"]
        for r in rows:
            cur.execute("""
                INSERT INTO diet_plan_meals (diet_plan_id, fdc_id, day_number, meal_slot, order_in_day)
                VALUES (%s,%s,%s,%s,%s)
            """, (plan_id, r["fdc_id"], r["day_number"], r["meal_slot"], r["order_in_day"]))

    return _fetch_diet_plan(db, plan_id)


@router.get("/plans/diet/latest")
def latest_diet_plan(user=Depends(get_current_user), db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT id FROM diet_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No diet plan yet")
    return _fetch_diet_plan(db, row["id"])


def _fetch_diet_plan(db, plan_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM diet_plans WHERE id = %s", (plan_id,))
        plan = cur.fetchone()
        cur.execute("""
            SELECT dpm.*, fc.name, fc.calories, fc.protein_g, fc.carbs_g, fc.fat_g, fc.fiber_g
            FROM diet_plan_meals dpm
            JOIN foods_cache fc ON fc.fdc_id = dpm.fdc_id
            WHERE dpm.diet_plan_id = %s
            ORDER BY dpm.order_in_day
        """, (plan_id,))
        meals = cur.fetchall()
    return {**plan, "meals": meals}
'''


from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
import json
from db import get_db
from auth import get_current_user
from agents.workout_planner import generate_workout_plan
from agents.diet_planner import generate_diet_plan
from agents.review_agent import generate_weekly_review, aggregate_week

router = APIRouter(prefix="/api", tags=["plans"])


def _get_profile(db, user_id):
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.user_id, p.height_cm, p.current_weight_kg, p.target_weight_kg, p.age, p.gender,
                   p.activity_level, h.knee_problems, h.back_pain, h.joint_pain,
                   f.primary_goal, f.experience_level, f.gym_availability, f.equipment_available, f.days_per_week,
                   d.diet_type, d.food_allergies, d.meals_per_day
            FROM profiles p
            LEFT JOIN health_assessments h ON h.user_id = p.user_id
            LEFT JOIN fitness_prefs f ON f.user_id = p.user_id
            LEFT JOIN diet_prefs d ON d.user_id = p.user_id
            WHERE p.user_id = %s
        """, (user_id,))
        row = cur.fetchone()

    if not row:
        return None

    # Convert row to dictionary and safely force integer parsing for split/meal preferences
    profile = dict(row)
    
    try:
        profile["days_per_week"] = int(profile.get("days_per_week") or 4)
    except (TypeError, ValueError):
        profile["days_per_week"] = 4

    try:
        profile["meals_per_day"] = int(profile.get("meals_per_day") or 5)
    except (TypeError, ValueError):
        profile["meals_per_day"] = 5

    return profile

def _get_latest_analysis(db, user_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM body_analysis WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        return cur.fetchone()


def _get_latest_review(db, user_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM weekly_reviews WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        return cur.fetchone()


@router.get("/review/weekly")
def weekly_review(user=Depends(get_current_user), db=Depends(get_db)):
    uid = user["id"]
    today = date.today()
    week_start = today - timedelta(days=6)  # Covers exactly 7 days including today

    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM weekly_reviews 
            WHERE user_id = %s AND week_start = %s 
            ORDER BY id DESC LIMIT 1
        """, (uid, week_start))
        existing_review = cur.fetchone()

        if existing_review:
            return existing_review

        cur.execute("""
            SELECT * FROM habit_logs 
            WHERE user_id = %s AND log_date >= %s AND log_date <= %s
            ORDER BY log_date
        """, (uid, week_start, today))
        logs = cur.fetchall()

    review = generate_weekly_review(logs)

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO weekly_reviews (user_id, week_start, stats, plateau_detected, summary)
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING id, user_id, week_start, stats, plateau_detected, summary, created_at
        """, (
            uid, 
            week_start, 
            json.dumps(review["stats"]), 
            review["plateau_detected"], 
            review["summary"]
        ))
        saved_row = cur.fetchone()

    return saved_row


@router.post("/plans/workout")
def create_workout_plan(user=Depends(get_current_user), db=Depends(get_db)):
    profile = _get_profile(db, user["id"])
    if not profile:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    review = _get_latest_review(db, user["id"])

    rows = generate_workout_plan(db, profile, review)
    if not rows:
        raise HTTPException(status_code=422, detail="No matching exercises found — try syncing exercises first")

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO workout_plans (user_id, week_start, based_on_review_id) VALUES (%s,%s,%s) RETURNING id
        """, (user["id"], date.today(), review["id"] if review else None))
        plan_id = cur.fetchone()["id"]
        for r in rows:
            cur.execute("""
                INSERT INTO workout_plan_exercises (workout_plan_id, wger_id, day_number, sets, reps, rest_seconds, order_in_day)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (plan_id, r["wger_id"], r["day_number"], r["sets"], r["reps"], r["rest_seconds"], r["order_in_day"]))

    return _fetch_workout_plan(db, plan_id)


@router.get("/plans/workout/latest")
def latest_workout_plan(user=Depends(get_current_user), db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT id FROM workout_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No workout plan yet")
    return _fetch_workout_plan(db, row["id"])


def _fetch_workout_plan(db, plan_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM workout_plans WHERE id = %s", (plan_id,))
        plan = cur.fetchone()
        cur.execute("""
            SELECT wpe.*, ec.name, ec.muscle_group, ec.instructions, ec.image_url
            FROM workout_plan_exercises wpe
            JOIN exercises_cache ec ON ec.wger_id = wpe.wger_id
            WHERE wpe.workout_plan_id = %s
            ORDER BY wpe.day_number, wpe.order_in_day
        """, (plan_id,))
        exercises = cur.fetchall()

    days = {}
    for ex in exercises:
        days.setdefault(ex["day_number"], []).append(ex)
    return {**plan, "days": [{"day_number": d, "exercises": ex} for d, ex in sorted(days.items())]}


@router.post("/plans/diet")
def create_diet_plan(user=Depends(get_current_user), db=Depends(get_db)):
    profile = _get_profile(db, user["id"])
    analysis = _get_latest_analysis(db, user["id"])
    if not profile or not analysis:
        raise HTTPException(status_code=400, detail="Complete onboarding first")
    review = _get_latest_review(db, user["id"])

    rows = generate_diet_plan(db, profile, analysis, review)
    if not rows:
        raise HTTPException(status_code=422, detail="No matching foods found — try syncing foods first")

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO diet_plans (user_id, week_start, based_on_review_id) VALUES (%s,%s,%s) RETURNING id
        """, (user["id"], date.today(), review["id"] if review else None))
        plan_id = cur.fetchone()["id"]
        for r in rows:
            cur.execute("""
                INSERT INTO diet_plan_meals (diet_plan_id, fdc_id, day_number, meal_slot, order_in_day)
                VALUES (%s,%s,%s,%s,%s)
            """, (plan_id, r["fdc_id"], r["day_number"], r["meal_slot"], r["order_in_day"]))

    return _fetch_diet_plan(db, plan_id)


@router.get("/plans/diet/latest")
def latest_diet_plan(user=Depends(get_current_user), db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT id FROM diet_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No diet plan yet")
    return _fetch_diet_plan(db, row["id"])


def _fetch_diet_plan(db, plan_id):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM diet_plans WHERE id = %s", (plan_id,))
        plan = cur.fetchone()
        cur.execute("""
            SELECT dpm.*, fc.name, fc.calories, fc.protein_g, fc.carbs_g, fc.fat_g, fc.fiber_g
            FROM diet_plan_meals dpm
            JOIN foods_cache fc ON fc.fdc_id = dpm.fdc_id
            WHERE dpm.diet_plan_id = %s
            ORDER BY dpm.order_in_day
        """, (plan_id,))
        meals = cur.fetchall()
    return {**plan, "meals": meals}