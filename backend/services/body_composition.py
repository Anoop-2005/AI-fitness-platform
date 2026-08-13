import math
from datetime import date, timedelta


def estimate_body_fat_pct(gender: str, height_cm: float, waist_cm: float, neck_cm: float = 0) -> float:
    """Estimate body fat percentage using standard US Navy formulas."""
    if waist_cm <= 0 or height_cm <= 0:
        return 0.0

    gender = (gender or "").lower()

    if gender == "male":
        if neck_cm > 0:
            return 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm) + 0.15456 * math.log10(height_cm)) - 450
        else:
            ratio = waist_cm / height_cm
            return 1.20 * (ratio * 100) + 0.23 * (height_cm / 100) - 16.2
            
    elif gender == "female":
        if neck_cm > 0:
            return 495 / (1.29579 - 0.35004 * math.log10(waist_cm - neck_cm) + 0.22100 * math.log10(height_cm)) - 450
        else:
            ratio = waist_cm / height_cm
            return 1.20 * (ratio * 100) + 0.23 * (height_cm / 100) - 5.4
            
    return 0.0


def classify_body_fat(gender: str, body_fat_pct: float) -> str:
    """Classify body fat percentage into fitness categories."""
    gender = (gender or "").lower()

    if gender == "male":
        if body_fat_pct < 6: return "Essential fat"
        if body_fat_pct < 14: return "Athletic"
        if body_fat_pct < 18: return "Fit"
        if body_fat_pct < 25: return "Average"
        return "Above average"
        
    elif gender == "female":
        if body_fat_pct < 14: return "Essential fat"
        if body_fat_pct < 21: return "Athletic"
        if body_fat_pct < 25: return "Fit"
        if body_fat_pct < 32: return "Average"
        return "Above average"
        
    return "Unknown"


def analyze_body_composition(db, user_id: str) -> dict:
    """Analyze body composition from metrics and return user insights."""
    from services.profile_helpers import get_profile

    profile = get_profile(db, user_id)
    if not profile:
        return {"error": "Profile not found"}

    gender = profile.get("gender", "")
    height_cm = profile.get("height_cm", 0)
    goal = profile.get("primary_goal", "general")

    with db.cursor() as cur:
        # Get latest waist measurement
        cur.execute("""
            SELECT waist_cm FROM habit_logs
            WHERE user_id = %s AND waist_cm IS NOT NULL
            ORDER BY log_date DESC LIMIT 1
        """, (user_id,))
        latest = cur.fetchone()
        waist_cm = latest.get("waist_cm", 0) if latest else 0

        # Get progress photos count
        cur.execute("SELECT COUNT(*) as count FROM progress_photos WHERE user_id = %s", (user_id,))
        photo_count = cur.fetchone()["count"]

        # Get weight trend (30 days)
        cur.execute("""
            SELECT weight_kg FROM habit_logs
            WHERE user_id = %s AND log_date >= %s AND weight_kg IS NOT NULL
            ORDER BY log_date DESC LIMIT 30
        """, (user_id, date.today() - timedelta(days=30)))
        weight_logs = cur.fetchall()

    # Determine weight trend direction
    weight_trend = "stable"
    if len(weight_logs) >= 2:
        recent = weight_logs[0].get("weight_kg", 0)
        older = weight_logs[-1].get("weight_kg", 0)
        if recent < older - 0.5:
            weight_trend = "decreasing"
        elif recent > older + 0.5:
            weight_trend = "increasing"

    insights = []

    # 1. Body fat estimate
    if waist_cm > 0 and height_cm > 0:
        bf = estimate_body_fat_pct(gender, height_cm, waist_cm)
        classification = classify_body_fat(gender, bf)
        insights.append({
            "type": "body_fat_estimate",
            "note": f"Estimated body fat: {round(bf, 1)}% ({classification}). Informational only."
        })

    # 2. Waist-to-height ratio
    if waist_cm > 0 and height_cm > 0:
        ratio = waist_cm / height_cm
        health_risk = "low" if ratio < 0.4 else ("moderate" if ratio < 0.5 else ("elevated" if ratio < 0.6 else "high"))
        insights.append({
            "type": "waist_height_ratio",
            "note": f"Waist-to-height ratio: {round(ratio, 2)} ({health_risk} health risk range)."
        })

    # 3. Weight trend alignment
    if weight_trend != "stable":
        direction = "down" if weight_trend == "decreasing" else "up"
        is_aligned = (goal in ("weight_loss", "fat_loss") and direction == "down") or (goal == "muscle_gain" and direction == "up")
        note_text = f"Weight is {weight_trend} — aligned with your goal!" if is_aligned else f"Weight is {weight_trend} — may need adjustment."
        insights.append({
            "type": "weight_trend",
            "note": note_text
        })

    # 4. Photo tracking
    if photo_count > 0:
        insights.append({
            "type": "photo_tracking",
            "note": f"You have {photo_count} progress photo(s). Take front/side/back photos monthly for best tracking."
        })

    return {
        "disclaimer": "These insights are informational only and not medical advice.",
        "insights": insights
    }