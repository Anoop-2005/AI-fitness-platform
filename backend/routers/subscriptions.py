"""
Subscription plan endpoints (mock).
Plans are fixed tiers; no real payment processing.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from db import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


@router.get("/plans")
def list_plans(user=Depends(get_current_user), db=Depends(get_db)):
    """List all active subscription plans."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT * FROM subscription_plans
            WHERE is_active = TRUE
            ORDER BY price_monthly
        """)
        return cur.fetchall()


@router.get("/my")
def my_subscription(user=Depends(get_current_user), db=Depends(get_db)):
    """Get current user's subscription."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT us.*, sp.name as plan_name, sp.description, sp.price_monthly, sp.features
            FROM user_subscriptions us
            JOIN subscription_plans sp ON sp.id = us.plan_id
            WHERE us.user_id = %s AND us.status = 'active'
            ORDER BY us.created_at DESC
            LIMIT 1
        """, (user["id"],))
        return cur.fetchone()


class SubscribeRequest(BaseModel):
    plan_id: int


@router.post("/subscribe")
def subscribe(body: SubscribeRequest, user=Depends(get_current_user), db=Depends(get_db)):
    """Subscribe to a plan (mock)."""
    from datetime import datetime, timedelta

    with db.cursor() as cur:
        # Get plan details
        cur.execute("SELECT * FROM subscription_plans WHERE id = %s AND is_active = TRUE", (body.plan_id,))
        plan = cur.fetchone()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")

        # Cancel any existing active subscription
        cur.execute("""
            UPDATE user_subscriptions SET status = 'cancelled'
            WHERE user_id = %s AND status = 'active'
        """, (user["id"],))

        # Calculate expiry
        duration = plan.get("duration_days", 30) if isinstance(plan, dict) else plan[3]
        expires = datetime.now() + timedelta(days=duration)

        cur.execute("""
            INSERT INTO user_subscriptions (user_id, plan_id, status, expires_at)
            VALUES (%s, %s, 'active', %s)
            RETURNING id, user_id, plan_id, status, expires_at
        """, (user["id"], body.plan_id, expires))

        return cur.fetchone()


@router.post("/cancel")
def cancel_subscription(user=Depends(get_current_user), db=Depends(get_db)):
    """Cancel current subscription."""
    with db.cursor() as cur:
        cur.execute("""
            UPDATE user_subscriptions SET status = 'cancelled'
            WHERE user_id = %s AND status = 'active'
        """, (user["id"],))
    return {"success": True}
