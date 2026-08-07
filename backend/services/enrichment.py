"""
Enriches exercises and foods with AI-generated details (calories, mistakes, safety, etc.).
Uses LLM when available, falls back to deterministic placeholders in MOCK_MODE.
Follows the same pattern as llm_client.chat() — degrades gracefully without API key.
"""
import json
from services.llm_client import chat, MOCK_MODE


def generate_exercise_enrichment(name: str, muscle_group: str, instructions: str) -> dict:
    """Generate calories, mistakes, safety, alternatives, progression for an exercise."""
    if MOCK_MODE:
        return _default_exercise_enrichment(name, muscle_group)

    prompt = f"""Given this exercise, provide enrichment data as JSON:
Exercise: {name}
Muscle Group: {muscle_group}
Instructions: {instructions or 'N/A'}

Return ONLY a JSON object with these exact keys:
- calories_per_minute: number (estimated kcal burned per minute for average person)
- common_mistakes: string (2-3 common form mistakes)
- safety_precautions: string (2-3 safety tips)
- alternative_exercises: string (2-3 alternative exercise names)
- progression_tips: string (2-3 ways to progress)

Example: {{"calories_per_minute": 8.5, "common_mistakes": "...", "safety_precautions": "...", "alternative_exercises": "...", "progression_tips": "..."}}"""

    try:
        response = chat(prompt)
        cleaned = response.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        data = json.loads(cleaned)
        return {
            "calories_per_minute": float(data.get("calories_per_minute", 5.0)),
            "common_mistakes": str(data.get("common_mistakes", "")),
            "safety_precautions": str(data.get("safety_precautions", "")),
            "alternative_exercises": str(data.get("alternative_exercises", "")),
            "progression_tips": str(data.get("progression_tips", "")),
        }
    except Exception:
        return _default_exercise_enrichment(name, muscle_group)


def _default_exercise_enrichment(name: str, muscle_group: str) -> dict:
    """Placeholder enrichment when no LLM key is set."""
    return {
        "calories_per_minute": 5.0,
        "common_mistakes": f"Maintain proper form during {name}. Avoid using momentum.",
        "safety_precautions": "Warm up before starting. Stop if you feel pain.",
        "alternative_exercises": f"Consult your trainer for {muscle_group} alternatives.",
        "progression_tips": "Gradually increase weight or reps over time.",
    }


def generate_food_enrichment(name: str, calories: float) -> dict:
    """Generate ingredients, recipe, cooking time, alternatives for a food."""
    if MOCK_MODE:
        return _default_food_enrichment(name)

    prompt = f"""Given this food item, provide enrichment data as JSON:
Food: {name}
Calories: {calories} kcal per serving

Return ONLY a JSON object with these exact keys:
- ingredients: string (comma-separated main ingredients)
- recipe: string (brief 2-3 sentence preparation method)
- cooking_time_minutes: integer (estimated cooking time in minutes)
- healthier_alternatives: string (1-2 healthier swap suggestions)

Example: {{"ingredients": "chicken breast, olive oil, salt", "recipe": "Grill the chicken.", "cooking_time_minutes": 15, "healthier_alternatives": "Use turkey instead."}}"""

    try:
        response = chat(prompt)
        cleaned = response.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        data = json.loads(cleaned)
        return {
            "ingredients": str(data.get("ingredients", "")),
            "recipe": str(data.get("recipe", "")),
            "cooking_time_minutes": int(data.get("cooking_time_minutes", 15)),
            "healthier_alternatives": str(data.get("healthier_alternatives", "")),
        }
    except Exception:
        return _default_food_enrichment(name)


def _default_food_enrichment(name: str) -> dict:
    """Placeholder enrichment when no LLM key is set."""
    return {
        "ingredients": f"Standard ingredients for {name}",
        "recipe": f"Prepare {name} according to standard cooking methods.",
        "cooking_time_minutes": 15,
        "healthier_alternatives": "Ask your nutritionist for healthier swaps.",
    }


def get_exercise_substitutions(db, muscle_group: str, equipment_available: list = None, limit: int = 3) -> list:
    """Find substitute exercises for a given muscle group from the cache."""
    query = "SELECT wger_id, name, muscle_group FROM exercises_cache WHERE muscle_group = %s"
    params = [muscle_group]

    with db.cursor() as cur:
        cur.execute(query, params)
        exercises = cur.fetchall()

    if equipment_available is not None:
        allowed = set(e.lower() for e in equipment_available) | {"none", "bodyweight"}
        filtered = []
        for ex in exercises:
            ex_equip = ex.get("equipment", []) if isinstance(ex, dict) else []
            if not ex_equip or all((e or "").lower() in allowed for e in ex_equip):
                filtered.append(ex)
        exercises = filtered

    return exercises[:limit]


def generate_motivational_message(user_name: str, streak: int, goal: str, adherence_pct: float) -> str:
    """Generate a personalized motivational message based on user progress."""
    if MOCK_MODE:
        return _default_motivational_message(user_name, streak, goal)

    prompt = f"""Write a short (1-2 sentence) personalized motivational message for:
Name: {user_name}
Current streak: {streak} days
Goal: {goal}
Weekly adherence: {adherence_pct}%

Be encouraging, specific to their progress, and actionable. Don't use emojis."""

    try:
        msg = chat(prompt)
        return msg.strip()
    except Exception:
        return _default_motivational_message(user_name, streak, goal)


def _default_motivational_message(user_name: str, streak: int, goal: str) -> str:
    """Placeholder motivational message."""
    if streak > 7:
        return f" Amazing streak, {user_name}! {streak} days strong — your {goal} is within reach!"
    elif streak > 3:
        return f"Keep it up, {user_name}! You're building momentum toward your {goal}."
    elif streak > 0:
        return f"Good start, {user_name}! Consistency is key to achieving your {goal}."
    else:
        return f"Today is a fresh start, {user_name}! Let's work toward your {goal}."
