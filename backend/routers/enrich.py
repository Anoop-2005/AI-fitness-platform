"""
On-demand enrichment for exercises and foods.
Generates calories, mistakes, safety, alternatives, progression (exercises)
and ingredients, recipe, cooking time, alternatives (foods) using LLM.
Results are cached in the DB columns to avoid repeated LLM calls.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import get_db
from auth import get_current_user
from services.enrichment import generate_exercise_enrichment, generate_food_enrichment

router = APIRouter(prefix="/api/enrich", tags=["enrich"])


@router.get("/exercise/{wger_id}")
def enrich_exercise(wger_id: int, user=Depends(get_current_user), db=Depends(get_db)):
    """Get enriched exercise data (calories, mistakes, safety, alternatives, progression)."""
    with db.cursor() as cur:
        cur.execute("SELECT * FROM exercises_cache WHERE wger_id = %s", (wger_id,))
        exercise = cur.fetchone()

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # Return cached enrichment if already present
    if exercise.get("common_mistakes"):
        return {
            "wger_id": exercise["wger_id"],
            "name": exercise["name"],
            "calories_per_minute": exercise.get("calories_per_minute"),
            "common_mistakes": exercise.get("common_mistakes"),
            "safety_precautions": exercise.get("safety_precautions"),
            "alternative_exercises": exercise.get("alternative_exercises"),
            "progression_tips": exercise.get("progression_tips"),
            "cached": True,
        }

    # Generate enrichment on-demand
    enrichment = generate_exercise_enrichment(
        name=exercise["name"],
        muscle_group=exercise.get("muscle_group", ""),
        instructions=exercise.get("instructions", ""),
    )

    # Cache the result
    with db.cursor() as cur:
        cur.execute("""
            UPDATE exercises_cache SET
                calories_per_minute = %s,
                common_mistakes = %s,
                safety_precautions = %s,
                alternative_exercises = %s,
                progression_tips = %s
            WHERE wger_id = %s
        """, (
            enrichment["calories_per_minute"],
            enrichment["common_mistakes"],
            enrichment["safety_precautions"],
            enrichment["alternative_exercises"],
            enrichment["progression_tips"],
            wger_id,
        ))

    return {
        "wger_id": exercise["wger_id"],
        "name": exercise["name"],
        **enrichment,
        "cached": False,
    }


@router.get("/food/{fdc_id}")
def enrich_food(fdc_id: str, user=Depends(get_current_user), db=Depends(get_db)):
    """Get enriched food data (ingredients, recipe, cooking time, alternatives)."""
    with db.cursor() as cur:
        cur.execute("SELECT * FROM foods_cache WHERE fdc_id = %s", (fdc_id,))
        food = cur.fetchone()

    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    # Return cached enrichment if already present
    if food.get("ingredients"):
        return {
            "fdc_id": food["fdc_id"],
            "name": food["name"],
            "ingredients": food.get("ingredients"),
            "recipe": food.get("recipe"),
            "cooking_time_minutes": food.get("cooking_time_minutes"),
            "healthier_alternatives": food.get("healthier_alternatives"),
            "cached": True,
        }

    # Generate enrichment on-demand
    enrichment = generate_food_enrichment(
        name=food["name"],
        calories=food.get("calories", 0),
    )

    # Cache the result
    with db.cursor() as cur:
        cur.execute("""
            UPDATE foods_cache SET
                ingredients = %s,
                recipe = %s,
                cooking_time_minutes = %s,
                healthier_alternatives = %s
            WHERE fdc_id = %s
        """, (
            enrichment["ingredients"],
            enrichment["recipe"],
            enrichment["cooking_time_minutes"],
            enrichment["healthier_alternatives"],
            fdc_id,
        ))

    return {
        "fdc_id": food["fdc_id"],
        "name": food["name"],
        **enrichment,
        "cached": False,
    }
