"""
Weekly review as a 2-node LangGraph: aggregate (pure arithmetic) -> narrate
(LLM writes a sentence about those exact numbers, nothing else).
"""
from typing import TypedDict

from langgraph.graph import StateGraph, END

from services.llm_client import chat, LLMUnavailableError


class ReviewState(TypedDict):
    logs: list[dict]
    stats: dict
    summary: str


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
    
    # Sort logs chronologically (oldest first) so changes calculate correctly
    sorted_logs = sorted(logs, key=lambda x: x.get("log_date", ""))
    n = len(sorted_logs)
    
    weights = []
    waists = []
    
    workout_done_count = 0
    total_water = 0.0
    total_sleep = 0.0
    total_steps = 0
    total_calories = 0.0
    total_protein = 0.0

    for l in sorted_logs:
        if isinstance(l, dict):
            if l.get("workout_done"): 
                workout_done_count += 1
            
            # Safely parse numeric fields, handling potential strings or bad input
            total_water += float(l.get("water_l", 0) or 0)
            
            # Clean up negative or erroneous sleep data if necessary
            sleep = float(l.get("sleep_hours", 0) or 0)
            total_sleep += max(0.0, sleep) 
            
            total_steps += int(l.get("steps", 0) or 0)
            total_calories += float(l.get("calories_consumed", 0) or 0)
            total_protein += float(l.get("protein_g", 0) or 0)

            w = l.get("weight_kg")
            if w is not None:
                weights.append(float(w))

            waist = l.get("waist_cm")
            if waist is not None:
                waists.append(float(waist))

    return {
        "workout_completion_pct": round(workout_done_count / n * 100, 1) if n > 0 else 0,
        "avg_water_l": round(total_water / n, 2) if n > 0 else 0,
        "avg_sleep_hours": round(total_sleep / n, 1) if n > 0 else 0,
        "avg_steps": round(total_steps / n) if n > 0 else 0,
        "avg_calories_consumed": round(total_calories / n) if n > 0 else 0,
        "avg_protein_g": round(total_protein / n, 1) if n > 0 else 0,
        "weight_change_kg": round(weights[-1] - weights[0], 2) if len(weights) >= 2 else 0,
        "waist_change_cm": round(waists[-1] - waists[0], 1) if len(waists) >= 2 else 0,
        "plateau_detected": detect_plateau(weights) if weights else False,
    }

def _aggregate_node(state: ReviewState) -> dict:
    return {"stats": aggregate_week(state["logs"])}


def _narrate_node(state: ReviewState) -> dict:
    if not state["stats"]:
        return {"summary": "No logs yet this week — start tracking to see a review."}

    stats = state["stats"]
    allowed_fields = ", ".join(stats.keys())

    try:
        summary = chat(
            f"Here is a user's weekly fitness data as a JSON object: {stats}\n\n"
            f"Write a short, supportive 3-sentence weekly review using ONLY the values in this JSON. "
            f"The ONLY fields that exist are: {allowed_fields}. "
            f"Do NOT mention diet adherence, calorie targets, percentage deviations, or any other "
            f"metric that is not one of these exact fields. "
            f"If plateau_detected is true, gently mention it."
        )
        # Safety net: if the model invents a metric we know doesn't exist in the
        # data, don't show it to the user — fall back to a plain, guaranteed-accurate
        # summary built directly from the real numbers instead.
        banned_phrases = ["diet adherence", "adherence", "target calories", "deviation"]
        if any(phrase in summary.lower() for phrase in banned_phrases):
            summary = _fallback_summary(stats)
    except LLMUnavailableError:
        # AI is down/rate-limited — never save a raw error as the summary.
        summary = _fallback_summary(stats)

    return {"summary": summary}


def _fallback_summary(stats: dict) -> str:
    """Deterministic, always-accurate summary built only from real stats.
    Used when the AI's output can't be trusted."""
    parts = [f"You completed {stats.get('workout_completion_pct', 0)}% of your workouts this week."]
    if stats.get("avg_water_l"):
        parts.append(f"Average water intake was {stats['avg_water_l']}L per day.")
    if stats.get("weight_change_kg"):
        direction = "lost" if stats["weight_change_kg"] < 0 else "gained"
        parts.append(f"You {direction} {abs(stats['weight_change_kg'])}kg this week.")
    if stats.get("plateau_detected"):
        parts.append("Your progress may be plateauing — worth reviewing your plan.")
    return " ".join(parts)


def build_review_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("aggregate", _aggregate_node)
    graph.add_node("narrate", _narrate_node)
    graph.set_entry_point("aggregate")
    graph.add_edge("aggregate", "narrate")
    graph.add_edge("narrate", END)
    return graph.compile()


def generate_weekly_review(logs: list[dict]) -> dict:
    result = build_review_graph().invoke({"logs": logs})
    stats = result["stats"]
    return {"stats": stats, "plateau_detected": stats.get("plateau_detected", False), "summary": result["summary"]}
