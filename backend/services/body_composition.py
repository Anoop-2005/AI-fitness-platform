"""
Body composition insights (heuristic-based, informational only).
Analyzes user metrics and progress photos to provide body composition observations.
NOT medical diagnosis — informational only.
"""
import math
from datetime import date, timedelta


def estimate_body_fat_pct(gender: str, height_cm: float, waist_cm: float, neck_cm: float = 0) -> float:
    """Estimate body fat % using US Navy method (heuristic)."""
    if waist_cm <= 0 or height_cm <= 0:
        return 0

    gender = (gender or "").lower()

    if gender == "male":
        if neck_cm > 0:
            # US Navy method for men
            return 495 / (1.0324 - 0.19077 * math.log10(waist_cm - neck_cm) + 0.15456 * math.log10(height_cm)) - 450
        else:
            # Simplified estimate using waist-to-height ratio
            ratio = waist_cm / height_cm
            return 1.20 * (ratio * 100) + 0.23 * (height_cm / 100) - 16.2
    elif gender == "female":
        if neck_cm > 0:
            return 495 / (1.29579 - 0.35004 * math.log10(waist_cm + 0 - neck_cm) + 0.22100 * math.log10(height_cm)) - 450
        else:
            ratio = waist_cm / height_cm
            return 1.20 * (ratio * 100) + 0.23 * (height_cm / 100) - 5.4
    else:
        ratio = waist_cm / height_cm
        return 1.20 * (ratio * 100) + 0.23 * (height_cm / 100) - 10


def classify_body_fat(gender: str, body_fat_pct: float) -> str:
    """Classify body fat percentage into categories."""
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
    else:
        if body_fat_pct < 10: return "Essential fat"
        if body_fat_pct < 17: return "Athletic"
        if body_fat_pct < 22: return "Fit"
        if body_fat_pct < 28: return "Average"
        return "Above average"


def analyze_body_composition(db, user_id: str) -> dict:
    """Analyze body composition from metrics and photos."""
    from services.profile_helpers import get_profile

    profile = get_profile(db, user_id)
    if not profile:
        return {"error": "Profile not found"}

    gender = profile.get("gender", "")
    height_cm = profile.get("height_cm", 0)
    current_weight = profile.get("current_weight_kg", 0)
    target_weight = profile.get("target_weight_kg", 0)

    # Get latest measurements from habit logs
    with db.cursor() as cur:
        cur.execute("""
            SELECT waist_cm, weight_kg, log_date FROM habit_logs
            WHERE user_id = %s AND waist_cm IS NOT NULL
            ORDER BY log_date DESC LIMIT 1
        """, (user_id,))
        latest = cur.fetchone()

    waist_cm = latest.get("waist_cm", 0) if latest else 0

    # Get progress photos count
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) as count FROM progress_photos WHERE user_id = %s", (user_id,))
        photo_count = cur.fetchone()["count"]

    # Get weight trend (30 days)
    with db.cursor() as cur:
        cur.execute("""
            SELECT weight_kg FROM habit_logs
            WHERE user_id = %s AND log_date >= %s AND weight_kg IS NOT NULL
            ORDER BY log_date DESC LIMIT 30
        """, (user_id, date.today() - timedelta(days=30)))
        weight_logs = cur.fetchall()

    weight_trend = "stable"
    if len(weight_logs) >= 2:
        recent = weight_logs[0].get("weight_kg", 0) if isinstance(weight_logs[0], dict) else 0
        older = weight_logs[-1].get("weight_kg", 0) if isinstance(weight_logs[-1], dict) else 0
        if recent < older - 0.5:
            weight_trend = "decreasing"
        elif recent > older + 0.5:
            weight_trend = "increasing"

    insights = []

    # Body fat estimate
    if waist_cm > 0 and height_cm > 0:
        bf = estimate_body_fat_pct(gender, height_cm, waist_cm)
        classification = classify_body_fat(gender, bf)
        insights.append({
            "type": "body_fat_estimate",
            "value": round(bf, 1),
            "classification": classification,
            "note": f"Estimated body fat: {round(bf, 1)}% ({classification}). Informational only."
        })

    # Waist-to-height ratio
    if waist_cm > 0 and height_cm > 0:
        ratio = waist_cm / height_cm
        if ratio < 0.4:
            health_risk = "low"
        elif ratio < 0.5:
            health_risk = "moderate"
        elif ratio < 0.6:
            health_risk = "elevated"
        else:
            health_risk = "high"
        insights.append({
            "type": "waist_height_ratio",
            "value": round(ratio, 3),
            "health_risk": health_risk,
            "note": f"Waist-to-height ratio: {round(ratio, 2)} ({health_risk} health risk range)."
        })

    # Weight trend
    if weight_trend != "stable":
        direction = "down" if weight_trend == "decreasing" else "up"
        goal = profile.get("primary_goal", "general")
        if (goal in ("weight_loss", "fat_loss") and direction == "down") or \
           (goal == "muscle_gain" and direction == "up"):
            insights.append({
                "type": "weight_trend",
                "trend": weight_trend,
                "note": f"Weight is {weight_trend} — aligned with your goal!"
            })
        else:
            insights.append({
                "type": "weight_trend",
                "trend": weight_trend,
                "note": f"Weight is {weight_trend} — may need adjustment."
            })

    # Photo tracking
    if photo_count > 0:
        insights.append({
            "type": "photo_tracking",
            "count": photo_count,
            "note": f"You have {photo_count} progress photo(s). Take front/side/back photos monthly for best tracking."
        })

    return {
        "disclaimer": "These insights are informational only and not medical advice.",
        "insights": insights,
        "metrics": {
            "height_cm": height_cm,
            "current_weight_kg": current_weight,
            "target_weight_kg": target_weight,
            "waist_cm": waist_cm,
            "weight_trend": weight_trend,
            "photo_count": photo_count,
        }
    }
