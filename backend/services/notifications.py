"""
Smart notification service.
Generates reminders based on user behavior and schedule.
Types: workout_reminder, meal_reminder, water_reminder, sleep_reminder, weekly_checkin, progress_photo, motivational_tip
"""
from datetime import date, timedelta
from services.llm_client import chat, MOCK_MODE


def generate_motivational_tip() -> str:
    """Generate a daily motivational tip."""
    if MOCK_MODE:
        return "Consistency is key! Show up today, even if it's just for 10 minutes."

    prompt = "Write one short (1-2 sentence) motivational fitness tip. Be encouraging and actionable."
    try:
        tip = chat(prompt)
        return tip.strip()
    except Exception:
        return "Consistency is key! Show up today, even if it's just for 10 minutes."


def check_and_create_reminders(db, user_id: str) -> list:
    """Check user activity and create relevant reminders."""
    notifications = []

    today = date.today()

    # Check if user logged workout today
    with db.cursor() as cur:
        cur.execute("""
            SELECT workout_done FROM habit_logs
            WHERE user_id = %s AND log_date = %s
        """, (user_id, today))
        today_log = cur.fetchone()

    if not today_log or not today_log.get("workout_done"):
        notifications.append({
            "type": "workout_reminder",
            "title": "Time to move!",
            "message": "You haven't logged a workout today. Even a short session counts!",
        })

    # Check water intake
    if today_log:
        water = today_log.get("water_l", 0) or 0
        if water < 2:
            notifications.append({
                "type": "water_reminder",
                "title": "Stay hydrated!",
                "message": f"You've logged {water}L water today. Aim for at least 2-3L!",
            })

    # Weekly check-in reminder (on Sundays)
    if today.weekday() == 6:
        notifications.append({
            "type": "weekly_checkin",
            "title": "Weekly check-in",
            "message": "It's time for your weekly review! Check your progress and plan for next week.",
        })

    # Motivational tip (daily)
    existing_tip = False
    with db.cursor() as cur:
        cur.execute("""
            SELECT id FROM notifications
            WHERE user_id = %s AND type = 'motivational_tip' AND created_at::date = %s
            LIMIT 1
        """, (user_id, today))
        existing_tip = cur.fetchone()

    if not existing_tip:
        tip = generate_motivational_tip()
        notifications.append({
            "type": "motivational_tip",
            "title": "Daily Motivation",
            "message": tip,
        })

    # Save notifications to DB
    created = []
    for n in notifications:
        with db.cursor() as cur:
            cur.execute("""
                INSERT INTO notifications (user_id, type, title, message, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                RETURNING id, user_id, type, title, message, read, created_at
            """, (user_id, n["type"], n["title"], n["message"]))
            created.append(cur.fetchone())

    return created
