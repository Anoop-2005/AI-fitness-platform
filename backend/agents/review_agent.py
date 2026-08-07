"""
Weekly review as a 2-node LangGraph: aggregate (pure arithmetic) -> narrate
(LLM writes a sentence about those exact numbers, nothing else).
"""
from typing import TypedDict

from langgraph.graph import StateGraph, END

from services.llm_client import chat


class ReviewState(TypedDict):
    logs: list[dict]
    stats: dict
    summary: str
    target_calories: float


def detect_plateau(weight_series: list[float]) -> bool:
    if len(weight_series) < 3:
        return False
    start, end = weight_series[0], weight_series[-1]
    if start == 0:
        return False
    return abs(end - start) / start < 0.003


'''def aggregate_week(logs: list[dict]) -> dict:
    if not logs:
        return {}
    n = len(logs)
    weights = [l["weight_kg"] for l in logs if l.get("weight_kg")]
    return {
        "workout_completion_pct": round(sum(1 for l in logs if l["workout_done"]) / n * 100, 1),
        "avg_water_l": round(sum(l["water_l"] for l in logs) / n, 2),
        "avg_sleep_hours": round(sum(l["sleep_hours"] for l in logs) / n, 1),
        "avg_steps": round(sum(l["steps"] for l in logs) / n),
        "avg_calories_consumed": round(sum(l["calories_consumed"] for l in logs) / n),
        "avg_protein_g": round(sum(l["protein_g"] for l in logs) / n, 1),
        "weight_change_kg": round(weights[-1] - weights[0], 2) if len(weights) >= 2 else 0,
        "plateau_detected": detect_plateau(weights) if weights else False,
    }
'''
def aggregate_week(logs: list[dict]) -> dict:
    if not logs:
        return {}
    n = len(logs)
    
    weights = []
    for l in logs:
        # Handle both dictionary access and tuple access safely
        if isinstance(l, dict):
            w = l.get("weight_kg")
        else:
            # If it's a tuple, find weight_kg based on table column order or safe extraction
            # Assuming weight_kg is in the row, or we fallback safely. 
            # Better yet, ensure your db connection uses RealDictCursor.
            try:
                w = l[logs[0].keys().index("weight_kg")] if hasattr(logs[0], "keys") else None
            except Exception:
                w = None
        if w is not None:
            weights.append(float(w))

    # Helper lambda to safely extract values whether row is dict or tuple
    def get_val(row, key, default=0):
        if isinstance(row, dict):
            return row.get(key, default)
        return default # Fallback if purely tuple-based without column names

    # Safely compute metrics handling both dicts and objects/tuples
    workout_done_count = 0
    total_water = 0.0
    total_sleep = 0.0
    total_steps = 0
    total_calories = 0.0
    total_protein = 0.0

    for l in logs:
        if isinstance(l, dict):
            if l.get("workout_done"): workout_done_count += 1
            total_water += float(l.get("water_l", 0) or 0)
            total_sleep += float(l.get("sleep_hours", 0) or 0)
            total_steps += int(l.get("steps", 0) or 0)
            total_calories += float(l.get("calories_consumed", 0) or 0)
            total_protein += float(l.get("protein_g", 0) or 0)

    # Compute waist change
    waists = []
    for l in logs:
        if isinstance(l, dict):
            w = l.get("waist_cm")
            if w is not None:
                waists.append(float(w))
    waist_change_cm = round(waists[-1] - waists[0], 1) if len(waists) >= 2 else 0

    # Compute total calories burned
    total_calories_burned = 0.0
    for l in logs:
        if isinstance(l, dict):
            total_calories_burned += float(l.get("calories_burned", 0) or 0)

    return {
        "workout_completion_pct": round(workout_done_count / n * 100, 1) if n > 0 else 0,
        "avg_water_l": round(total_water / n, 2) if n > 0 else 0,
        "avg_sleep_hours": round(total_sleep / n, 1) if n > 0 else 0,
        "avg_steps": round(total_steps / n) if n > 0 else 0,
        "avg_calories_consumed": round(total_calories / n) if n > 0 else 0,
        "avg_protein_g": round(total_protein / n, 1) if n > 0 else 0,
        "weight_change_kg": round(weights[-1] - weights[0], 2) if len(weights) >= 2 else 0,
        "waist_change_cm": waist_change_cm,
        "total_calories_burned": round(total_calories_burned),
        "plateau_detected": detect_plateau(weights) if weights else False,
    }

def _aggregate_node(state: ReviewState) -> dict:
    return {"stats": aggregate_week(state["logs"])}


def _narrate_node(state: ReviewState) -> dict:
    if not state["stats"]:
        return {"summary": "No logs yet this week — start tracking to see a review."}
    target_calories = state.get("target_calories")
    calorie_note = ""
    if target_calories:
        avg_consumed = state["stats"].get("avg_calories_consumed", 0)
        if avg_consumed > 0:
            adherence_pct = round(min(target_calories / avg_consumed * 100, 100) if avg_consumed > target_calories else round(avg_consumed / target_calories * 100, 1))
            calorie_note = f" Diet adherence: {adherence_pct}% (target {target_calories} kcal, avg {avg_consumed} kcal)."

    summary = chat(
        f"Write a short, supportive 3-sentence weekly review using ONLY these numbers, "
        f"don't invent anything not listed here: {state['stats']}. "
        f"If plateau_detected is true, gently mention it.{calorie_note}"
    )
    return {"summary": summary}


def build_review_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("aggregate", _aggregate_node)
    graph.add_node("narrate", _narrate_node)
    graph.set_entry_point("aggregate")
    graph.add_edge("aggregate", "narrate")
    graph.add_edge("narrate", END)
    return graph.compile()


def generate_weekly_review(logs: list[dict], target_calories: float = 0) -> dict:
    result = build_review_graph().invoke({"logs": logs, "target_calories": target_calories})
    stats = result["stats"]
    return {"stats": stats, "plateau_detected": stats.get("plateau_detected", False), "summary": result["summary"]}
