"""
Smart notification endpoints.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from db import get_db
from auth import get_current_user
from services.notifications import check_and_create_reminders

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/")
def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Get user notifications, optionally filtered to unread only."""
    query = "SELECT * FROM notifications WHERE user_id = %s"
    params = [user["id"]]

    if unread_only:
        query += " AND read = FALSE"

    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    with db.cursor() as cur:
        cur.execute(query, params)
        notifications = cur.fetchall()

    # Also check for new reminders
    check_and_create_reminders(db, user["id"])

    # Re-fetch after potential new notifications
    with db.cursor() as cur:
        cur.execute(query, params)
        notifications = cur.fetchall()

    return notifications


@router.post("/check")
def trigger_check(user=Depends(get_current_user), db=Depends(get_db)):
    """Manually trigger notification check (generates new reminders)."""
    new_notifications = check_and_create_reminders(db, user["id"])
    return {"created": len(new_notifications), "notifications": new_notifications}


class MarkReadRequest(BaseModel):
    notification_id: int


@router.post("/mark-read")
def mark_read(
    body: MarkReadRequest,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Mark a notification as read."""
    with db.cursor() as cur:
        cur.execute("""
            UPDATE notifications SET read = TRUE
            WHERE id = %s AND user_id = %s
            RETURNING id
        """, (body.notification_id, user["id"]))
        if not cur.fetchone():
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}


@router.post("/mark-all-read")
def mark_all_read(user=Depends(get_current_user), db=Depends(get_db)):
    """Mark all notifications as read."""
    with db.cursor() as cur:
        cur.execute("""
            UPDATE notifications SET read = TRUE
            WHERE user_id = %s AND read = FALSE
        """, (user["id"],))
    return {"success": True}


@router.get("/unread-count")
def unread_count(user=Depends(get_current_user), db=Depends(get_db)):
    """Get count of unread notifications."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) as count FROM notifications
            WHERE user_id = %s AND read = FALSE
        """, (user["id"],))
        row = cur.fetchone()
    return {"count": row["count"] if row else 0}
