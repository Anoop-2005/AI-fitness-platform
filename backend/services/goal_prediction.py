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

    target_weight = float(profile.get("target_weight_kg", 0) or 0)
    timeline = analysis.get("timeline_weeks", {})

    # Get actual weight progress from habit logs (last 30 days)
    cutoff = date.today() - timedelta(days=30)
    with db.cursor() as cur:
        cur.execute("""
            SELECT log_date, weight_kg FROM habit_logs
            WHERE user_id = %s AND log_date >= %s AND weight_kg IS NOT NULL
            ORDER BY log_date ASC
        """, (user_id, cutoff))
        weight_logs = cur.fetchall()

    # Determine current weight dynamically from the latest log, falling back to profile
    if weight_logs:
        latest_entry = weight_logs[-1]
        raw_current = latest_entry["weight_kg"] if isinstance(latest_entry, dict) else latest_entry.get("weight_kg", 0)
        current_weight = float(raw_current or profile.get("current_weight_kg", 0))
    else:
        current_weight = float(profile.get("current_weight_kg", 0) or 0)

    if not current_weight or not target_weight:
        return {"error": "Weight data missing"}

    weight_diff = abs(target_weight - current_weight)

    # Calculate actual weekly rate of change
    actual_weekly_change = 0.0
    if len(weight_logs) >= 2:
        first_entry = weight_logs[0]
        last_entry = weight_logs[-1]
        
        first_weight = float((first_entry.get("weight_kg") if isinstance(first_entry, dict) else 0) or 0)
        last_weight = float((last_entry.get("weight_kg") if isinstance(last_entry, dict) else 0) or 0)
        
        first_date = first_entry.get("log_date") if isinstance(first_entry, dict) else None
        last_date = last_entry.get("log_date") if isinstance(last_entry, dict) else None

        if first_date and last_date and first_weight > 0 and last_weight > 0:
            days_diff = (last_date - first_date).days
            if days_diff > 0:
                actual_weekly_change = ((last_weight - first_weight) / days_diff) * 7

    # Use actual rate if available, otherwise use timeline estimate
    goal = profile.get("primary_goal", "general_fitness")
    is_loss = goal in ("weight_loss", "fat_loss", "body_recomposition")

    if actual_weekly_change != 0:
        weekly_change = actual_weekly_change
    else:
        expected_weeks = float(timeline.get("expected_weeks", 12) or 12)
        weekly_change = -(weight_diff / expected_weeks) if is_loss else (weight_diff / expected_weeks)

    # Predicted completion date
    if abs(weekly_change) > 0.01:
        weeks_remaining = weight_diff / abs(weekly_change)
        predicted_date = date.today() + timedelta(weeks=int(weeks_remaining))
    else:
        predicted_date = None
        weeks_remaining = float(timeline.get("expected_weeks", 12) or 12)

    # Goal achievement percentage calculation
    achievement_pct = 0.0
    if len(weight_logs) > 0:
        initial_weight = float(weight_logs[0].get("weight_kg", current_weight) or current_weight)
        total_change_needed = abs(target_weight - initial_weight)
        
        if total_change_needed > 0:
            change_made = abs(current_weight - initial_weight)
            # Check if movement is in the right direction towards the target
            moving_correctly = (initial_weight > target_weight and current_weight <= initial_weight) or \
                               (initial_weight < target_weight and current_weight >= initial_weight)
            if moving_correctly:
                achievement_pct = min(round((change_made / total_change_needed) * 100, 1), 100.0)

    # Plateau detection: if actual change < 30% of expected over recent logs
    plateau_detected = False
    if len(weight_logs) >= 3:
        expected_weekly = weight_diff / float(timeline.get("expected_weeks", 12) or 12)
        if expected_weekly > 0 and abs(actual_weekly_change) < abs(expected_weekly) * 0.3:
            plateau_detected = True

    return {
        "current_weight_kg": round(current_weight, 1),
        "target_weight_kg": round(target_weight, 1),
        "weight_diff_kg": round(weight_diff, 1),
        "predicted_completion_date": predicted_date.isoformat() if predicted_date else None,
        "weeks_remaining": int(weeks_remaining),
        "weekly_weight_change_kg": round(weekly_change, 2),
        "monthly_projection_kg": round(weekly_change * 4.33, 1),
        "goal_achievement_pct": achievement_pct,
        "plateau_detected": plateau_detected,
        "goal": goal,
    }