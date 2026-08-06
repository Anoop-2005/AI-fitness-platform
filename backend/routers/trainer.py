"""
Trainer dashboard endpoints. Protected by trainer role check.
Allows trainers to view their assigned clients, their plans, progress, and send messages.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from db import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/trainer", tags=["trainer"])


def require_trainer(user=Depends(get_current_user), db=Depends(get_db)):
    """Verify the current user has trainer role."""
    if user.get("role") != "trainer":
        raise HTTPException(status_code=403, detail="Trainer access required")
    return user


@router.get("/clients")
def get_assigned_clients(
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get all clients assigned to this trainer."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.user_id, p.full_name, p.age, p.gender, p.height_cm,
                   p.current_weight_kg, p.target_weight_kg, p.activity_level,
                   u.created_at,
                   u.email
            FROM trainer_clients tc
            JOIN profiles p ON p.user_id = tc.client_id
            LEFT JOIN auth.users u ON u.id = p.user_id
            WHERE tc.trainer_id = %s
            ORDER BY p.full_name
        """, (user["id"],))
        return cur.fetchall()


@router.get("/clients/{client_id}/profile")
def get_client_profile(
    client_id: str,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get detailed profile for a specific client."""
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
        """, (client_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


@router.get("/clients/{client_id}/workout")
def get_client_workout(
    client_id: str,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get current workout plan for a client."""
    with db.cursor() as cur:
        cur.execute("SELECT id FROM workout_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (client_id,))
        row = cur.fetchone()
        if not row:
            return {"days": []}

        cur.execute("""
            SELECT wpe.*, ec.name, ec.muscle_group, ec.instructions, ec.image_url
            FROM workout_plan_exercises wpe
            JOIN exercises_cache ec ON ec.wger_id = wpe.wger_id
            WHERE wpe.workout_plan_id = %s
            ORDER BY wpe.day_number, wpe.order_in_day
        """, (row["id"],))
        exercises = cur.fetchall()

    days = {}
    for ex in exercises:
        days.setdefault(ex["day_number"], []).append(ex)
    return {"days": [{"day_number": d, "exercises": ex} for d, ex in sorted(days.items())]}


@router.get("/clients/{client_id}/diet")
def get_client_diet(
    client_id: str,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get current diet plan for a client."""
    with db.cursor() as cur:
        cur.execute("SELECT id FROM diet_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (client_id,))
        row = cur.fetchone()
        if not row:
            return {"meals": []}

        cur.execute("""
            SELECT dpm.*, fc.name, fc.calories, fc.protein_g, fc.carbs_g, fc.fat_g, fc.fiber_g
            FROM diet_plan_meals dpm
            JOIN foods_cache fc ON fc.fdc_id = dpm.fdc_id
            WHERE dpm.diet_plan_id = %s
            ORDER BY dpm.order_in_day
        """, (row["id"],))
        meals = cur.fetchall()

    return {"meals": meals}


@router.get("/clients/{client_id}/progress")
def get_client_progress(
    client_id: str,
    days: int = 30,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get progress data for a client."""
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=min(days, 365))

    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM habit_logs
            WHERE user_id = %s AND log_date >= %s
            ORDER BY log_date DESC
        """, (client_id, cutoff))
        logs = cur.fetchall()

    return logs


@router.get("/clients/{client_id}/analysis")
def get_client_analysis(
    client_id: str,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get body analysis for a client."""
    with db.cursor() as cur:
        cur.execute("SELECT * FROM body_analysis WHERE user_id = %s ORDER BY id DESC LIMIT 1", (client_id,))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No analysis found")
    return row


class SendMessageRequest(BaseModel):
    client_id: str
    message: str


@router.post("/messages")
def send_message(
    body: SendMessageRequest,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Send a message to a client."""
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO trainer_messages (trainer_id, client_id, message, sent_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id, trainer_id, client_id, message, sent_at
        """, (user["id"], body.client_id, body.message))
        row = cur.fetchone()
    return row


@router.get("/messages/{client_id}")
def get_messages(
    client_id: str,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get message history with a client."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM trainer_messages
            WHERE trainer_id = %s AND client_id = %s
            ORDER BY sent_at DESC
            LIMIT 50
        """, (user["id"], client_id))
        return cur.fetchall()


# 1. Get trainer info for a client
@router.get("/my-trainer")
def get_my_trainer(user=Depends(get_current_user), db=Depends(get_db)):
    """Get the trainer assigned to this client."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.user_id, p.full_name, p.age, p.gender
            FROM trainer_clients tc
            JOIN profiles p ON p.user_id = tc.trainer_id
            WHERE tc.client_id = %s
            LIMIT 1
        """, (user["id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No trainer assigned")
    return row


# 2. Get messages between client and their trainer
@router.get("/my-messages")
def get_my_messages(user=Depends(get_current_user), db=Depends(get_db)):
    """Get all messages between this client and their trainer."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM trainer_messages
            WHERE client_id = %s
            ORDER BY sent_at ASC
            LIMIT 100
        """, (user["id"],))
        return cur.fetchall()


# 3. Client sends message back to trainer
class ClientMessageRequest(BaseModel):
    message: str

@router.post("/my-messages")
def client_send_message(
    body: ClientMessageRequest,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Client sends a message to their trainer."""
    # Find the trainer for this client
    with db.cursor() as cur:
        cur.execute("""
            SELECT trainer_id FROM trainer_clients WHERE client_id = %s LIMIT 1
        """, (user["id"],))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="No trainer assigned")
        trainer_id = row["trainer_id"] if isinstance(row, dict) else row[0]

        cur.execute("""
            INSERT INTO trainer_messages (trainer_id, client_id, message, sent_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id, trainer_id, client_id, message, sent_at
        """, (trainer_id, user["id"], body.message))
        return cur.fetchone()


@router.get("/messages/{client_id}")
def get_messages(
    client_id: str,
    user=Depends(require_trainer),
    db=Depends(get_db)
):
    """Get message history with a client."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM trainer_messages
            WHERE trainer_id = %s AND client_id = %s
            ORDER BY sent_at ASC
            LIMIT 50
        """, (user["id"], client_id))
        return cur.fetchall()