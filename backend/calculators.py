"""
Deterministic body/nutrition math. No LLM, no database — just formulas.
These are the numbers the rest of the app treats as ground truth.
"""

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9,
}

GOAL_CALORIE_ADJUSTMENT = {
    "weight_loss": -0.20, "fat_loss": -0.20, "muscle_gain": 0.12, "strength": 0.08,
    "body_recomposition": -0.05, "athletic_performance": 0.05, "general_fitness": 0.0,
}


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5: return "Underweight"
    if bmi < 25: return "Normal"
    if bmi < 30: return "Overweight"
    return "Obese"


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """Mifflin-St Jeor equation."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    if gender.lower() == "male":
        return round(base + 5, 1)
    if gender.lower() == "female":
        return round(base - 161, 1)
    return round(base - 78, 1)  # gender-neutral average of the two offsets


def calculate_tdee(bmr: float, activity_level: str) -> float:
    return round(bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.375), 1)


def calculate_target_calories(tdee: float, goal: str) -> float:
    return round(tdee * (1 + GOAL_CALORIE_ADJUSTMENT.get(goal, 0.0)), 1)


def calculate_macros(target_calories: float, weight_kg: float, goal: str) -> dict:
    protein_per_kg = 2.2 if goal in ("weight_loss", "fat_loss", "body_recomposition") else \
        2.0 if goal in ("muscle_gain", "strength", "athletic_performance") else 1.6
    protein_g = round(protein_per_kg * weight_kg, 1)
    fat_g = round((target_calories * 0.25) / 9, 1)
    carbs_g = round(max(target_calories - protein_g * 4 - fat_g * 9, 0) / 4, 1)
    fiber_g = round(target_calories / 1000 * 14, 1)
    return {"protein_g": protein_g, "carbs_g": carbs_g, "fat_g": fat_g, "fiber_g": fiber_g}


def calculate_water_intake_l(weight_kg: float, activity_level: str) -> float:
    base = weight_kg * 0.033
    if activity_level in ("active", "very_active"):
        base += 0.5
    return round(base, 2)


def estimate_timeline_weeks(current_weight_kg: float, target_weight_kg: float, goal: str) -> dict:
    """A range, not a promise — safe rates of change per week."""
    diff = abs(target_weight_kg - current_weight_kg)
    if diff == 0:
        return {"best_case_weeks": 0, "expected_weeks": 0, "conservative_weeks": 0}

    if goal in ("weight_loss", "fat_loss", "body_recomposition"):
        fast_rate, slow_rate = current_weight_kg * 0.01, current_weight_kg * 0.005
    else:
        fast_rate, slow_rate = current_weight_kg * 0.005, current_weight_kg * 0.0025

    best_case = max(round(diff / fast_rate), 1)
    conservative = round(diff / slow_rate)
    return {"best_case_weeks": best_case, "expected_weeks": round((best_case + conservative) / 2),
             "conservative_weeks": conservative}


def full_body_analysis(weight_kg, height_cm, age, gender, activity_level, goal, target_weight_kg) -> dict:
    bmi = calculate_bmi(weight_kg, height_cm)
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)
    target_calories = calculate_target_calories(tdee, goal)
    return {
        "bmi": bmi, "bmi_category": bmi_category(bmi), "bmr": bmr, "tdee": tdee,
        "target_calories": target_calories,
        "macros": calculate_macros(target_calories, weight_kg, goal),
        "water_l": calculate_water_intake_l(weight_kg, activity_level),
        "timeline_weeks": estimate_timeline_weeks(weight_kg, target_weight_kg, goal),
    }
