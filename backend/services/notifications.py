from datetime import date, timedelta


def _already_sent_today(db, user_id: str, notif_type: str) -> bool:
    with db.cursor() as cur:
        cur.execute("""
            SELECT id FROM notifications
            WHERE user_id = %s AND type = %s AND notif_date = CURRENT_DATE
            LIMIT 1
        """, (user_id, notif_type))
        return cur.fetchone() is not None


def check_and_create_reminders(db, user_id: str) -> list:
    """Check today's activity and create any reminders not already sent today."""
    today = date.today()
    to_create = []

    with db.cursor() as cur:
        cur.execute("""
            SELECT workout_done, water_l FROM habit_logs
            WHERE user_id = %s AND log_date = %s
        """, (user_id, today))
        today_log = cur.fetchone()

    # Workout reminder
    if not _already_sent_today(db, user_id, "workout_reminder"):
        if not today_log or not today_log.get("workout_done"):
            to_create.append(("workout_reminder", "Time to move!",
                               "You haven't logged a workout today. Even a short session counts!"))

    # Water reminder
    if not _already_sent_today(db, user_id, "water_reminder"):
        water = (today_log.get("water_l") if today_log else 0) or 0
        if water < 2:
            to_create.append(("water_reminder", "Stay hydrated!",
                               f"You've logged {water}L today — aim for at least 2-3L."))

    # Weight logging reminder (no weight logged in the last 7 days)
    if not _already_sent_today(db, user_id, "weight_reminder"):
        with db.cursor() as cur:
            cur.execute("""
                SELECT id FROM habit_logs
                WHERE user_id = %s AND weight_kg IS NOT NULL AND log_date >= %s
                LIMIT 1
            """, (user_id, today - timedelta(days=7)))
            recent_weight = cur.fetchone()
        if not recent_weight:
            to_create.append(("weight_reminder", "Log your weight",
                               "You haven't logged your weight in over a week."))

    # Progress photo reminder (no photo uploaded in the last 14 days)
    if not _already_sent_today(db, user_id, "photo_reminder"):
        with db.cursor() as cur:
            cur.execute("""
                SELECT id FROM progress_photos
                WHERE user_id = %s AND uploaded_at >= %s
                LIMIT 1
            """, (user_id, today - timedelta(days=14)))
            recent_photo = cur.fetchone()
        if not recent_photo:
            to_create.append(("photo_reminder", "Snap a progress photo",
                               "It's been a while since your last progress photo."))

    # Weekly check-in reminder, once a week on Sunday
    if today.weekday() == 6 and not _already_sent_today(db, user_id, "weekly_checkin"):
        to_create.append(("weekly_checkin", "Weekly check-in",
                           "It's time for your weekly review — check your progress and plan next week."))

    created = []
    with db.cursor() as cur:
        for notif_type, title, message in to_create:
            cur.execute("""
                INSERT INTO notifications (user_id, type, title, message, notif_date)
                VALUES (%s, %s, %s, %s, CURRENT_DATE)
                ON CONFLICT (user_id, type, notif_date) DO NOTHING
                RETURNING id, user_id, type, title, message, read, created_at
            """, (user_id, notif_type, title, message))
            row = cur.fetchone()
            if row:
                created.append(row)

        return created