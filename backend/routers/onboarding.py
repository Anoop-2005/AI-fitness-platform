from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

from db import get_db
from auth import get_current_user
import calculators

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


class OnboardingRequest(BaseModel):
    full_name: str
    age: int
    gender: str
    height_cm: float
    current_weight_kg: float
    target_weight_kg: float
    occupation: Optional[str] = None
    activity_level: str
    sleep_hours: Optional[float] = None
    # health
    diabetes: bool = False
    blood_pressure: Optional[str] = None
    heart_disease: bool = False
    thyroid: bool = False
    asthma: bool = False
    joint_pain: bool = False
    knee_problems: bool = False
    back_pain: bool = False
    injuries: Optional[str] = None
    allergies: Optional[str] = None
    medications: Optional[str] = None
    smoking: bool = False
    alcohol: bool = False
    # fitness
    primary_goal: str
    experience_level: str
    gym_availability: Optional[str] = None
    equipment_available: list[str] = []
    days_per_week: int = 4
    session_minutes: int = 45
    # diet
    diet_type: str = "non_vegetarian"
    food_allergies: list[str] = []
    meals_per_day: int = 5
    budget_tier: str = "medium"


@router.post("")
def save_onboarding(body: OnboardingRequest, user=Depends(get_current_user), db=Depends(get_db)):
    uid = user["id"]
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO profiles (user_id, full_name, age, gender, height_cm, current_weight_kg,
                target_weight_kg, occupation, activity_level, sleep_hours)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (user_id) DO UPDATE SET
                full_name=excluded.full_name, age=excluded.age, gender=excluded.gender,
                height_cm=excluded.height_cm, current_weight_kg=excluded.current_weight_kg,
                target_weight_kg=excluded.target_weight_kg, occupation=excluded.occupation,
                activity_level=excluded.activity_level, sleep_hours=excluded.sleep_hours,
                updated_at=CURRENT_TIMESTAMP
        """, (uid, body.full_name, body.age, body.gender, body.height_cm, body.current_weight_kg,
              body.target_weight_kg, body.occupation, body.activity_level, body.sleep_hours))

        cur.execute("""
            INSERT INTO health_assessments (user_id, diabetes, blood_pressure, heart_disease, thyroid,
                asthma, joint_pain, knee_problems, back_pain, injuries, allergies, medications, smoking, alcohol)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (user_id) DO UPDATE SET
                diabetes=excluded.diabetes, blood_pressure=excluded.blood_pressure,
                heart_disease=excluded.heart_disease, thyroid=excluded.thyroid, asthma=excluded.asthma,
                joint_pain=excluded.joint_pain, knee_problems=excluded.knee_problems,
                back_pain=excluded.back_pain, injuries=excluded.injuries, allergies=excluded.allergies,
                medications=excluded.medications, smoking=excluded.smoking, alcohol=excluded.alcohol
        """, (uid, body.diabetes, body.blood_pressure, body.heart_disease, body.thyroid, body.asthma,
              body.joint_pain, body.knee_problems, body.back_pain, body.injuries, body.allergies,
              body.medications, body.smoking, body.alcohol))

        cur.execute("""
            INSERT INTO fitness_prefs (user_id, primary_goal, experience_level, gym_availability,
                equipment_available, days_per_week, session_minutes)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (user_id) DO UPDATE SET
                primary_goal=excluded.primary_goal, experience_level=excluded.experience_level,
                gym_availability=excluded.gym_availability, equipment_available=excluded.equipment_available,
                days_per_week=excluded.days_per_week, session_minutes=excluded.session_minutes
        """, (uid, body.primary_goal, body.experience_level, body.gym_availability,
              json.dumps(body.equipment_available), body.days_per_week, body.session_minutes))

        cur.execute("""
            INSERT INTO diet_prefs (user_id, diet_type, food_allergies, meals_per_day, budget_tier)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (user_id) DO UPDATE SET
                diet_type=excluded.diet_type, food_allergies=excluded.food_allergies,
                meals_per_day=excluded.meals_per_day, budget_tier=excluded.budget_tier
        """, (uid, body.diet_type, json.dumps(body.food_allergies), body.meals_per_day, body.budget_tier))

        analysis = calculators.full_body_analysis(
            weight_kg=body.current_weight_kg, height_cm=body.height_cm, age=body.age,
            gender=body.gender, activity_level=body.activity_level, goal=body.primary_goal,
            target_weight_kg=body.target_weight_kg,
        )
        cur.execute("""
            INSERT INTO body_analysis (user_id, bmi, bmr, tdee, target_calories, macros, water_l, timeline_weeks)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (uid, analysis["bmi"], analysis["bmr"], analysis["tdee"], analysis["target_calories"],
              json.dumps(analysis["macros"]), analysis["water_l"], json.dumps(analysis["timeline_weeks"])))

    return {"profile_saved": True, "body_analysis": analysis}


@router.get("")
def get_profile(user=Depends(get_current_user), db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.*, h.diabetes, h.blood_pressure, h.heart_disease, h.thyroid, h.asthma,
                   h.joint_pain, h.knee_problems, h.back_pain, h.injuries, h.allergies, h.medications,
                   h.smoking, h.alcohol,
                   f.primary_goal, f.experience_level, f.gym_availability, f.equipment_available,
                   f.days_per_week, f.session_minutes,
                   d.diet_type, d.food_allergies, d.meals_per_day, d.budget_tier
            FROM profiles p
            LEFT JOIN health_assessments h ON h.user_id = p.user_id
            LEFT JOIN fitness_prefs f ON f.user_id = p.user_id
            LEFT JOIN diet_prefs d ON d.user_id = p.user_id
            WHERE p.user_id = %s
        """, (user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No onboarding profile yet")
    return row


@router.get("/analysis")
def get_latest_analysis(user=Depends(get_current_user), db=Depends(get_db)):
    with db.cursor() as cur:
        cur.execute("SELECT * FROM body_analysis WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No body analysis yet")
    return row


@router.delete("")
def reset_onboarding(user=Depends(get_current_user), db=Depends(get_db)):
    """Deletes the user's profile so they can loop back through onboarding testing."""
    uid = user["id"]
    with db.cursor() as cur:
        # Cascade deletes or explicit deletions for user profile data
        cur.execute("DELETE FROM profiles WHERE user_id = %s", (uid,))
    return {"success": True, "message": "Onboarding data reset successfully"}