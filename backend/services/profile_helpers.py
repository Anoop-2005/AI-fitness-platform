from datetime import date, timedelta


def get_profile(db, user_id):
    """Fetch combined profile (personal + health + fitness + diet prefs) for a user."""
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


def get_latest_analysis(db, user_id):
    """Fetch the most recent body analysis for a user."""
    with db.cursor() as cur:
        cur.execute("SELECT * FROM body_analysis WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        return cur.fetchone()


def get_recent_habits(db, user_id, days=14):
    """Fetch recent habit logs for context."""
    cutoff = date.today() - timedelta(days=days-1)
    with db.cursor() as cur:
        cur.execute(
            "SELECT * FROM habit_logs WHERE user_id = %s AND log_date >= %s ORDER BY log_date ASC ",
            (user_id, cutoff),
        )
        return cur.fetchall()


def get_workout_plan_summary(db, user_id):
    """Get current workout plan summary as formatted text."""
    with db.cursor() as cur:
        cur.execute("SELECT id FROM workout_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        if not row:
            return "No workout plan generated yet."
        cur.execute("""
            SELECT wpe.*, ec.name, ec.muscle_group
            FROM workout_plan_exercises wpe
            JOIN exercises_cache ec ON ec.wger_id = wpe.wger_id
            WHERE wpe.workout_plan_id = %s
            ORDER BY wpe.day_number, wpe.order_in_day
        """, (row["id"],))
        exercises = cur.fetchall()
    if not exercises:
        return "Workout plan exists but has no exercises."
    days = {}
    for ex in exercises:
        days.setdefault(ex["day_number"], []).append(ex["name"])
    return "\n".join(f"Day {d}: {', '.join(names)}" for d, names in sorted(days.items()))


def get_diet_plan_summary(db, user_id):
    """Get current diet plan summary as formatted text."""
    with db.cursor() as cur:
        cur.execute("SELECT id FROM diet_plans WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        row = cur.fetchone()
        if not row:
            return "No diet plan generated yet."
        cur.execute("""
            SELECT dpm.*, fc.name
            FROM diet_plan_meals dpm
            JOIN foods_cache fc ON fc.fdc_id = dpm.fdc_id
            WHERE dpm.diet_plan_id = %s
            ORDER BY dpm.order_in_day
        """, (row["id"],))
        meals = cur.fetchall()
    if not meals:
        return "Diet plan exists but has no meals."
    return "\n".join(f"{m['meal_slot'].replace('_', ' ').title()}: {m['name']}" for m in meals)