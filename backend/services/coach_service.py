# backend/services/coach_service.py
from services.llm_client import chat
from routers.plans import _get_profile, _get_latest_analysis


def _get_recent_habits(db, user_id: str, days: int = 14) -> list:
    """Fetch recent habit logs for context."""
    from datetime import date, timedelta
    cutoff = date.today() - timedelta(days=days)
    with db.cursor() as cur:
        cur.execute(
            "SELECT * FROM habit_logs WHERE user_id = %s AND log_date >= %s ORDER BY log_date DESC LIMIT 14",
            (user_id, cutoff)
        )
        return cur.fetchall()


def _get_workout_plan_summary(db, user_id: str) -> str:
    """Get current workout plan summary."""
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


def _get_diet_plan_summary(db, user_id: str) -> str:
    """Get current diet plan summary."""
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


def get_coach_response(db, user_id: str, user_message: str) -> str:
    """Generate AI coach response with full user context."""
    profile = _get_profile(db, user_id)
    analysis = _get_latest_analysis(db, user_id)
    habits = _get_recent_habits(db, user_id)
    workout_summary = _get_workout_plan_summary(db, user_id)
    diet_summary = _get_diet_plan_summary(db, user_id)

    # Build context for the LLM
    context = f"""You are an AI personal fitness coach named 'Iron Coach'. You are supportive, knowledgeable, and motivating. You help users with:
- Answering fitness and nutrition questions
- Correcting workout techniques and form
- Suggesting exercise alternatives
- Explaining exercises and muscle groups
- Motivating users to stay consistent
- Adjusting training plans based on progress
- Recommending rest and recovery when needed
- Detecting signs of overtraining
- Providing daily motivational tips

USER PROFILE:
- Name: {profile.get('full_name', 'User') if profile else 'User'}
- Age: {profile.get('age', 'N/A') if profile else 'N/A'}
- Gender: {profile.get('gender', 'N/A') if profile else 'N/A'}
- Height: {profile.get('height_cm', 'N/A')} cm
- Current Weight: {profile.get('current_weight_kg', 'N/A')} kg
- Target Weight: {profile.get('target_weight_kg', 'N/A')} kg
- Activity Level: {profile.get('activity_level', 'N/A') if profile else 'N/A'}
- Primary Goal: {profile.get('primary_goal', 'N/A') if profile else 'N/A'}
- Experience Level: {profile.get('experience_level', 'N/A') if profile else 'N/A'}
- Gym: {profile.get('gym_availability', 'N/A') if profile else 'N/A'}

BODY ANALYSIS:
- BMI: {analysis.get('bmi', 'N/A') if analysis else 'N/A'} ({analysis.get('bmi_category', 'N/A') if analysis else 'N/A'})
- BMR: {analysis.get('bmr', 'N/A') if analysis else 'N/A'} kcal
- TDEE: {analysis.get('tdee', 'N/A') if analysis else 'N/A'} kcal
- Target Calories: {analysis.get('target_calories', 'N/A') if analysis else 'N/A'} kcal
- Macros: {analysis.get('macros', 'N/A') if analysis else 'N/A'}
- Water: {analysis.get('water_l', 'N/A') if analysis else 'N/A'}L/day

CURRENT WORKOUT PLAN:
{workout_summary}

CURRENT DIET PLAN:
{diet_summary}

RECENT HABIT LOGS (last 14 days):
- Workout days: {sum(1 for h in habits if h.get('workout_done'))}/{len(habits)} days
- Avg water: {round(sum(h.get('water_l', 0) for h in habits) / max(len(habits), 1), 1)}L/day
- Avg sleep: {round(sum(h.get('sleep_hours', 0) for h in habits) / max(len(habits), 1), 1)} hrs/night
- Avg steps: {round(sum(h.get('steps', 0) for h in habits) / max(len(habits), 1))}/day

IMPORTANT RULES:
1. Always prioritize safety - recommend rest if user shows signs of overtraining
2. Be encouraging but honest about progress
3. Suggest specific alternatives when correcting form
4. Keep responses concise and actionable (2-4 paragraphs max)
5. If user asks about medical issues, remind them this is not medical advice
6. Reference their actual data when giving personalized advice
7. Use simple, clear language - avoid overly technical jargon

USER MESSAGE: {user_message}"""

    return chat(context)