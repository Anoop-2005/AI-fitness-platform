"""
Admin panel endpoints. Protected by admin role check.
Allows listing and deleting users (trainers and clients).
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from db import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(user=Depends(get_current_user), db=Depends(get_db)):
    """Verify the current user has admin role."""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/users")
def list_users(
    role: Optional[str] = None,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """List all users, optionally filtered by role."""
    query = """
        SELECT p.user_id, p.full_name, p.age, p.gender, p.height_cm, 
               p.current_weight_kg, p.target_weight_kg, p.activity_level,
               u.created_at, p.role,
               u.email
        FROM profiles p
        LEFT JOIN auth.users u ON u.id = p.user_id
    """
    params = []

    if role:
        query += " WHERE p.role = %s"
        params.append(role)

    query += " ORDER BY p.created_at DESC"

    with db.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()
    return rows


@router.get("/trainers")
def list_trainers(user=Depends(require_admin), db=Depends(get_db)):
    """List all trainers."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.user_id, p.full_name, p.age, p.gender, u.created_at, p.role,
                   u.email
            FROM profiles p
            LEFT JOIN auth.users u ON u.id = p.user_id
            WHERE p.role = 'trainer'
            ORDER BY u.created_at DESC
        """)
        return cur.fetchall()


@router.get("/clients")
def list_clients(user=Depends(require_admin), db=Depends(get_db)):
    """List all clients (users with client role or no role)."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT p.user_id, p.full_name, p.age, p.gender, p.height_cm,
                   p.current_weight_kg, p.target_weight_kg, p.activity_level,
                   u.created_at, p.role,
                   u.email, f.primary_goal
            FROM profiles p
            LEFT JOIN auth.users u ON u.id = p.user_id
            LEFT JOIN fitness_prefs f ON f.user_id = p.user_id
            WHERE p.role IS NULL OR p.role = 'client'
            ORDER BY u.created_at DESC
        """)
        return cur.fetchall()


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """Delete a user and all their data."""
    with db.cursor() as cur:
        # Delete from all related tables
        cur.execute("DELETE FROM habit_logs WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM workout_plan_exercises WHERE workout_plan_id IN (SELECT id FROM workout_plans WHERE user_id = %s)", (user_id,))
        cur.execute("DELETE FROM workout_plans WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM diet_plan_meals WHERE diet_plan_id IN (SELECT id FROM diet_plans WHERE user_id = %s)", (user_id,))
        cur.execute("DELETE FROM diet_plans WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM body_analysis WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM health_assessments WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM fitness_prefs WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM diet_prefs WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM weekly_reviews WHERE user_id = %s", (user_id,))
        cur.execute("DELETE FROM profiles WHERE user_id = %s", (user_id,))

    return {"success": True, "message": "User deleted successfully"}


@router.get("/stats")
def get_stats(user=Depends(require_admin), db=Depends(get_db)):
    """Get platform statistics."""
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM profiles WHERE role = 'trainer'")
        trainer_count = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) as count FROM profiles WHERE role IS NULL OR role = 'client'")
        client_count = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) as count FROM profiles")
        total_users = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) as count FROM habit_logs WHERE log_date >= CURRENT_DATE - INTERVAL '30 days'")
        recent_logs = cur.fetchone()["count"]

    return {
        "trainers": trainer_count,
        "clients": client_count,
        "total_users": total_users,
        "recent_logs": recent_logs,
    }


# --- Exercise Library Management ---

@router.get("/exercises")
def admin_list_exercises(
    search: Optional[str] = None,
    muscle_group: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """List exercises with optional filtering."""
    query = "SELECT * FROM exercises_cache WHERE 1=1"
    params = []

    if search:
        query += " AND name ILIKE %s"
        params.append(f"%{search}%")
    if muscle_group:
        query += " AND muscle_group ILIKE %s"
        params.append(f"%{muscle_group}%")

    query += " ORDER BY name LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.put("/exercises/{wger_id}")
def admin_update_exercise(
    wger_id: int,
    body: dict,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """Update an exercise in the library."""
    allowed_fields = ["name", "muscle_group", "instructions", "image_url", "difficulty",
                      "common_mistakes", "safety_precautions", "alternative_exercises",
                      "progression_tips", "calories_per_minute"]
    updates = {k: v for k, v in body.items() if k in allowed_fields}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values()) + [wger_id]

    with db.cursor() as cur:
        cur.execute(f"UPDATE exercises_cache SET {set_clause} WHERE wger_id = %s RETURNING *", values)
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return row


@router.delete("/exercises/{wger_id}")
def admin_delete_exercise(
    wger_id: int,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """Delete an exercise from the library."""
    with db.cursor() as cur:
        cur.execute("DELETE FROM exercises_cache WHERE wger_id = %s RETURNING wger_id", (wger_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Exercise not found")
    return {"success": True}


# --- Food Library Management ---

@router.get("/foods")
def admin_list_foods(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """List foods with optional filtering."""
    query = "SELECT * FROM foods_cache WHERE 1=1"
    params = []

    if search:
        query += " AND name ILIKE %s"
        params.append(f"%{search}%")

    query += " ORDER BY name LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.put("/foods/{fdc_id}")
def admin_update_food(
    fdc_id: str,
    body: dict,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """Update a food in the library."""
    allowed_fields = ["name", "calories", "protein_g", "carbs_g", "fat_g", "fiber_g",
                      "serving_size", "ingredients", "recipe", "cooking_time_minutes",
                      "healthier_alternatives"]
    updates = {k: v for k, v in body.items() if k in allowed_fields}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values()) + [fdc_id]

    with db.cursor() as cur:
        cur.execute(f"UPDATE foods_cache SET {set_clause} WHERE fdc_id = %s RETURNING *", values)
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Food not found")
    return row


@router.delete("/foods/{fdc_id}")
def admin_delete_food(
    fdc_id: str,
    user=Depends(require_admin),
    db=Depends(get_db)
):
    """Delete a food from the library."""
    with db.cursor() as cur:
        cur.execute("DELETE FROM foods_cache WHERE fdc_id = %s RETURNING fdc_id", (fdc_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Food not found")
    return {"success": True}


# --- Subscription Plan Management ---

@router.get("/subscriptions/plans")
def admin_list_plans(user=Depends(require_admin), db=Depends(get_db)):
    """List all subscription plans."""
    with db.cursor() as cur:
        cur.execute("SELECT * FROM subscription_plans ORDER BY price_monthly")
        return cur.fetchall()


@router.post("/subscriptions/plans")
def admin_create_plan(body: dict, user=Depends(require_admin), db=Depends(get_db)):
    """Create a new subscription plan."""
    name = body.get("name", "")
    price = body.get("price_monthly", 0)
    duration = body.get("duration_days", 30)
    description = body.get("description", "")
    features = body.get("features", [])

    if not name:
        raise HTTPException(status_code=400, detail="Plan name required")

    import json
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO subscription_plans (name, description, price_monthly, duration_days, features)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
        """, (name, description, price, duration, json.dumps(features)))
        return cur.fetchone()


@router.delete("/subscriptions/plans/{plan_id}")
def admin_delete_plan(plan_id: int, user=Depends(require_admin), db=Depends(get_db)):
    """Deactivate a subscription plan."""
    with db.cursor() as cur:
        cur.execute("""
            UPDATE subscription_plans SET is_active = FALSE WHERE id = %s RETURNING id
        """, (plan_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Plan not found")
    return {"success": True}
