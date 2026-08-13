"""
Goal prediction service.
Computes expected completion date, weekly/monthly projections, and goal achievement %.
Uses deterministic math (no LLM ) based on the user's body_analysis timeline_weeks
and actual habit log progress.
"""
from datetime import date, timedelta
from services.profile_helpers import get_profile, get_latest_analysis


def compute_goal_prediction(db, user_id: str) -> dict:
    """Compute goal prediction based on user profile, analysis, and actual progress."""
    profile = get_profile(db, user_id)
    analysis = get_latest_analysis(db, user_id)

    if not profile or not analysis:
        return {"error": "Complete onboarding first"}

    current_weight = profile.get("current_weight_kg", 0)
    target_weight = profile.get("target_weight_kg", 0)
    timeline = analysis.get("timeline_weeks", {})
    macros = analysis.get("macros", {})

    if not current_weight or not target_weight:
        return {"error": "Weight data missing"}

    weight_diff = abs(target_weight - current_weight)

    # Get actual weight progress from habit logs (last 30 days)
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=30)
    with db.cursor() as cur:
        cur.execute("""
            SELECT log_date, weight_kg FROM habit_logs
            WHERE user_id = %s AND log_date >= %s AND weight_kg IS NOT NULL
            ORDER BY log_date ASC
        """, (user_id, cutoff))
        weight_logs = cur.fetchall()

    # Calculate actual weekly rate of change
    actual_weekly_change = 0
    if len(weight_logs) >= 2:
        first_weight = weight_logs[0]["weight_kg"] if isinstance(weight_logs[0], dict) else weight_logs[0].get("weight_kg", 0)
        last_weight = weight_logs[-1]["weight_kg"] if isinstance(weight_logs[-1], dict) else weight_logs[-1].get("weight_kg", 0)
        first_date = weight_logs[0]["log_date"] if isinstance(weight_logs[0], dict) else weight_logs[0].get("log_date")
        last_date = weight_logs[-1]["log_date"] if isinstance(weight_logs[-1], dict) else weight_logs[-1].get("log_date")

        if first_date and last_date:
            days_diff = (last_date - first_date).days if hasattr(last_date, 'days') else (last_date - first_date).days
            if days_diff > 0:
                actual_weekly_change = ((last_weight - first_weight) / days_diff) * 7

    # Use actual rate if available, otherwise use timeline estimate
    goal = profile.get("primary_goal", "general_fitness")
    is_loss = goal in ("weight_loss", "fat_loss", "body_recomposition")

    if actual_weekly_change != 0:
        weekly_change = actual_weekly_change
    else:
        # Estimate from timeline
        expected_weeks = timeline.get("expected_weeks", 12)
        weekly_change = -(weight_diff / expected_weeks) if is_loss else (weight_diff / expected_weeks)

    # Predicted completion date
    if weekly_change != 0:
        weeks_remaining = weight_diff / abs(weekly_change) if abs(weekly_change) > 0.01 else timeline.get("expected_weeks", 12)
        predicted_date = date.today() + timedelta(weeks=int(weeks_remaining))
    else:
        predicted_date = None
        weeks_remaining = timeline.get("expected_weeks", 12)

    # Goal achievement percentage
    total_change_needed = abs(target_weight - current_weight)
    if total_change_needed > 0 and actual_weekly_change != 0:
        starting_weight = current_weight
        if len(weight_logs) > 0:
            starting_weight = weight_logs[0]["weight_kg"] if isinstance(weight_logs[0], dict) else weight_logs[0].get("weight_kg", current_weight)
        change_made = abs(current_weight - starting_weight)
        achievement_pct = min(round(change_made / total_change_needed * 100, 1), 100)
    else:
        achievement_pct = 0

    # Plateau detection: if actual change < 50% of expected over 3 weeks
    plateau_detected = False
    if len(weight_logs) >= 3 and actual_weekly_change != 0:
        expected_weekly = weight_diff / timeline.get("expected_weeks", 12)
        if abs(actual_weekly_change) < abs(expected_weekly) * 0.3:
            plateau_detected = True

    return {
        "current_weight_kg": current_weight,
        "target_weight_kg": target_weight,
        "weight_diff_kg": round(weight_diff, 1),
        "predicted_completion_date": predicted_date.isoformat() if predicted_date else None,
        "weeks_remaining": int(weeks_remaining),
        "weekly_weight_change_kg": round(weekly_change, 2),
        "monthly_projection_kg": round(weekly_change * 4.33, 1),
        "goal_achievement_pct": achievement_pct,
        "plateau_detected": plateau_detected,
        "goal": goal,
    }