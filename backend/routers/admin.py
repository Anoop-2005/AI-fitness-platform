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
