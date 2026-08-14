import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from services.llm_client import chat


class DayPlanState(TypedDict):
    day_number: int
    muscle_groups: list[str]
    experience_level: str
    goal: str
    sets_base: int
    candidates: list[dict]
    llm_raw_response: str
    chosen: list[dict]


def get_candidate_exercises(db, muscle_groups: list[str], equipment_available: list[str] | None,
                             injury_flags: list[str]) -> list[dict]:
    # Expanded query mapping to prevent empty candidate lists on broad split days
    query = "SELECT wger_id, name, muscle_group, equipment FROM exercises_cache WHERE muscle_group = ANY(%s)"
    params = [muscle_groups]

    injury_keywords = {
        "knee": ["squat", "lunge", "leg press", "jump"],
        "back": ["deadlift", "row", "good morning"],
        "shoulder": ["overhead press", "lateral raise", "bench press"],
    }
    exclude_terms = [kw for flag in injury_flags for kw in injury_keywords.get(flag, [])]
    if exclude_terms:
        query += " AND NOT (" + " OR ".join(["name ILIKE %s"] * len(exclude_terms)) + ")"
        params.extend([f"%{term}%" for term in exclude_terms])

    with db.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    # If strict equipment filtering returns nothing, gracefully fall back to all rows to avoid empty screens
    if equipment_available is not None:
        allowed = set(e.lower() for e in equipment_available) | {"none", "bodyweight"}
        filtered_rows = [r for r in rows if not r["equipment"] or all((e or "").lower() in allowed for e in r["equipment"])]
        if filtered_rows:
            rows = filtered_rows

    return rows


def _parse_and_validate(llm_response: str, valid_ids: set[int], fallback: list[dict], sets_base: int) -> list[dict]:
    try:
        cleaned = llm_response.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        items = json.loads(cleaned)
        valid_items = [i for i in items if isinstance(i, dict) and i.get("wger_id") in valid_ids]
        if valid_items:
            return valid_items
    except Exception:
        pass
    
    # Safe fallback mapping ensuring up to 4 unique items are picked safely
    safe_fallback = fallback[:4] if len(fallback) >= 4 else fallback
    return [{"wger_id": c["wger_id"], "sets": sets_base, "reps": "8-10", "rest_seconds": 75} for c in safe_fallback]


def build_day_plan_graph(db, equipment_available: list[str] | None, injury_flags: list[str]):
    def fetch_candidates_node(state: DayPlanState) -> dict:
        candidates = get_candidate_exercises(db, state["muscle_groups"], equipment_available, injury_flags)
        return {"candidates": candidates}

    def llm_select_node(state: DayPlanState) -> dict:
        candidates = state["candidates"]
        if not candidates:
            return {"llm_raw_response": "[]"}
        candidate_list_text = "\n".join(f"- id={c['wger_id']}: {c['name']} ({c['muscle_group']})" for c in candidates)
        prompt = (
            f"You are picking exercises for a {state['experience_level']} lifter whose goal is "
            f"{state['goal']}. Choose 4 to 6 exercises from this list ONLY (use the exact id numbers):\n"
            f"{candidate_list_text}\n\n"
            f'Respond with ONLY a JSON array like [{{"wger_id": 123, "sets": {state["sets_base"]}, '
            f'"reps": "8-10", "rest_seconds": 75}}] — no other text.'
        )
        return {"llm_raw_response": chat(prompt)}

    def validate_node(state: DayPlanState) -> dict:
        valid_ids = {c["wger_id"] for c in state["candidates"]}
        chosen = _parse_and_validate(state["llm_raw_response"], valid_ids, state["candidates"], state["sets_base"])
        return {"chosen": chosen}

    graph = StateGraph(DayPlanState)
    graph.add_node("fetch_candidates", fetch_candidates_node)
    graph.add_node("llm_select", llm_select_node)
    graph.add_node("validate", validate_node)
    graph.set_entry_point("fetch_candidates")
    graph.add_edge("fetch_candidates", "llm_select")
    graph.add_edge("llm_select", "validate")
    graph.add_edge("validate", END)
    return graph.compile()


# Robust 7-day split mapping utilizing standard major and sub-muscle categories to guarantee data availability
DAY_SPLITS = {
    1: [["Chest", "Back", "Legs", "Shoulders"]],
    2: [["Chest", "Shoulders"], ["Back", "Legs"]],
    3: [["Chest", "Triceps"], ["Back", "Biceps"], ["Legs", "Shoulders"]],
    4: [["Chest", "Triceps"], ["Back", "Biceps"], ["Legs"], ["Shoulders"]],
    5: [["Chest"], ["Back"], ["Legs"], ["Shoulders"], ["Biceps", "Triceps"]],
    6: [["Chest"], ["Back"], ["Legs"], ["Shoulders"], ["Biceps"], ["Triceps"]],
    7: [["Chest"], ["Back"], ["Legs"], ["Shoulders"], ["Arms"], ["Legs"], ["Chest", "Back"]],
}


def generate_workout_plan(db, profile: dict, review: dict | None) -> list[dict]:
    try:
        days_per_week = int(profile.get("days_per_week", 7))
    except (TypeError, ValueError):
        days_per_week = 7

    days_per_week = max(1, min(days_per_week, 7))
    split = DAY_SPLITS[days_per_week]
    equipment = None if profile.get("gym_availability") == "Commercial Gym" else profile.get("equipment_available")

    injury_flags = []
    if profile.get("knee_problems"): injury_flags.append("knee")
    if profile.get("back_pain"): injury_flags.append("back")
    if profile.get("joint_pain"): injury_flags.append("shoulder")

    sets_base = {"Beginner": 3, "Intermediate": 4, "Advanced": 5}.get(profile["experience_level"], 3)
    if review:
        if review.get("plateau_detected") or review.get("stats", {}).get("workout_completion_pct", 100) < 50:
            sets_base = max(2, sets_base - 1)
        elif review.get("stats", {}).get("workout_completion_pct", 0) >= 90:
            sets_base = min(6, sets_base + 1)

    compiled_graph = build_day_plan_graph(db, equipment, injury_flags)

    plan_rows = []
    for day_number, muscle_groups in enumerate(split, start=1):
        # Fresh invocation state per day to completely prevent cross-day pollution
        result = compiled_graph.invoke({
            "day_number": day_number, 
            "muscle_groups": muscle_groups,
            "experience_level": profile["experience_level"], 
            "goal": profile["primary_goal"],
            "sets_base": sets_base,
            "candidates": [],
            "llm_raw_response": "",
            "chosen": []
        })
        
        chosen_items = result.get("chosen", [])
        for order, item in enumerate(chosen_items):
            plan_rows.append({
                "wger_id": item["wger_id"], 
                "day_number": day_number,
                "sets": item.get("sets", sets_base), 
                "reps": item.get("reps", "8-10"),
                "rest_seconds": item.get("rest_seconds", 75), 
                "order_in_day": order,
            })
            
    return plan_rows