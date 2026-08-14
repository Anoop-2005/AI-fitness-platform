import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from services.llm_client import chat

MEAL_SLOTS_BY_COUNT = {
    3: ["breakfast", "lunch", "dinner"],
    4: ["breakfast", "lunch", "snack", "dinner"],
    5: ["breakfast", "snack", "lunch", "dinner", "bedtime"],
    6: ["breakfast", "snack", "lunch", "post_workout", "dinner", "bedtime"],
    7: ["breakfast", "snack", "lunch", "post_workout", "dinner", "evening_snack", "bedtime"],
    8: ["breakfast", "morning_snack", "lunch", "afternoon_snack", "post_workout", "dinner", "evening_snack", "bedtime"],
}


class DietPlanState(TypedDict):
    slots: list[str]
    target_calories: float
    protein_g: float
    diet_type: str
    adherence_note: str
    candidates: list[dict]
    llm_raw_response: str
    chosen: list[dict]


def get_candidate_foods(db, exclude_terms: list[str], limit: int = 100) -> list[dict]:
    query = """
        SELECT fdc_id, name, calories, protein_g, carbs_g, fat_g, fiber_g 
        FROM foods_cache 
        WHERE name NOT ILIKE '%%mcdonald%%' 
          AND name NOT ILIKE '%%denny%%' 
          AND name NOT ILIKE '%%applebee%%'
          AND name NOT ILIKE '%%burger king%%'
          AND name NOT ILIKE '%%fat, %%'
          AND (name ILIKE '%%chicken%%' OR name ILIKE '%%rice%%' OR name ILIKE '%%egg%%' 
               OR name ILIKE '%%oats%%' OR name ILIKE '%%beef%%' OR name ILIKE '%%salmon%%' 
               OR name ILIKE '%%potato%%' OR name ILIKE '%%broccoli%%' OR name ILIKE '%%milk%%'
               OR name ILIKE '%%banana%%' OR name ILIKE '%%peanut butter%%')
    """
    params = []
    if exclude_terms:
        query += " AND NOT (" + " OR ".join(["name ILIKE %s"] * len(exclude_terms)) + ")"
        params.extend([f"%{term}%" for term in exclude_terms])
    
    query += " LIMIT %s"
    params.append(limit)
    
    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def _parse_and_validate(llm_response: str, valid_ids: set[str], fallback: list[dict], slots: list[str]) -> list[dict]:
    try:
        cleaned = llm_response.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        items = json.loads(cleaned)
        valid_items = [i for i in items if isinstance(i, dict) and str(i.get("fdc_id")) in valid_ids and i.get("meal_slot")]
        if valid_items:
            return valid_items
    except Exception:
        pass
    return [{"fdc_id": fallback[i % len(fallback)]["fdc_id"], "meal_slot": slot} for i, slot in enumerate(slots)]


def build_diet_plan_graph(db, exclude_terms: list[str]):
    def fetch_candidates_node(state: DietPlanState) -> dict:
        return {"candidates": get_candidate_foods(db, exclude_terms)}

    def llm_select_node(state: DietPlanState) -> dict:
        candidates = state["candidates"]
        if not candidates:
            return {"llm_raw_response": "[]"}
        candidate_list_text = "\n".join(
            f"- id={c['fdc_id']}: {c['name']} ({c['calories']} kcal, {c['protein_g']}g protein)" for c in candidates
        )
        prompt = (
            f"Pick one unique food for EACH of these specific meal slots: {', '.join(state['slots'])}. "
            f"Daily target is about {state['target_calories']} kcal and {state['protein_g']}g protein "
            f"({state['diet_type']} diet).{state['adherence_note']}\n\n"
            f"Choose ONLY from this list (use the exact id values):\n{candidate_list_text}\n\n"
            f'Respond with ONLY a JSON array mapping each slot, like: '
            f'[{{"fdc_id": "171077", "meal_slot": "{state["slots"][0]}"}}] — ensure every slot in the list is returned. No other text.'
        )
        return {"llm_raw_response": chat(prompt)}

    def validate_node(state: DietPlanState) -> dict:
        valid_ids = {c["fdc_id"] for c in state["candidates"]}
        chosen = _parse_and_validate(state["llm_raw_response"], valid_ids, state["candidates"], state["slots"])
        return {"chosen": chosen}

    graph = StateGraph(DietPlanState)
    graph.add_node("fetch_candidates", fetch_candidates_node)
    graph.add_node("llm_select", llm_select_node)
    graph.add_node("validate", validate_node)
    
    graph.set_entry_point("fetch_candidates")
    graph.add_edge("fetch_candidates", "llm_select")
    graph.add_edge("llm_select", "validate")
    graph.add_edge("validate", END)
    return graph.compile()


def generate_diet_plan(db, profile: dict, analysis: dict, review: dict | None) -> list[dict]:
    # Explicitly cast meals_per_day to integer to prevent lookup failures
    try:
        meals_per_day = int(profile.get("meals_per_day", 5))
    except (TypeError, ValueError):
        meals_per_day = 5

    slots = MEAL_SLOTS_BY_COUNT.get(meals_per_day, MEAL_SLOTS_BY_COUNT[5])
    allergies = profile.get("food_allergies") or []

    target_calories = analysis["target_calories"]
    adherence_note = ""
    if review and review.get("stats", {}).get("avg_calories_consumed"):
        avg = review["stats"]["avg_calories_consumed"]
        if avg > target_calories * 1.15:
            adherence_note = " Last week's logged intake ran high — lean toward the lower-calorie options."
        elif avg < target_calories * 0.85:
            adherence_note = " Last week's logged intake ran low — make sure meals aren't too light."

    compiled_graph = build_diet_plan_graph(db, allergies)
    result = compiled_graph.invoke({
        "slots": slots, "target_calories": target_calories, "protein_g": analysis["macros"]["protein_g"],
        "diet_type": profile["diet_type"], "adherence_note": adherence_note,
    })

    return [{"fdc_id": item["fdc_id"], "day_number": 1, "meal_slot": item["meal_slot"], "order_in_day": i}
            for i, item in enumerate(result["chosen"])]