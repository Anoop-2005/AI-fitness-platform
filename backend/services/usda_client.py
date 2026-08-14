import httpx
from config import USDA_API_KEY

USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

NUTRIENT_IDS = {"calories": 1008, "protein_g": 1003, "fat_g": 1004, "carbs_g": 1005, "fiber_g": 1079}


def _extract_nutrient(food_nutrients: list[dict], nutrient_id: int) -> float:
    for n in food_nutrients:
        if n.get("nutrientId") == nutrient_id:
            return n.get("value", 0)
    return 0


def parse_food(raw: dict) -> dict:
    nutrients = raw.get("foodNutrients", [])
    return {
        "fdc_id": str(raw["fdcId"]),
        "name": raw["description"],
        "calories": _extract_nutrient(nutrients, NUTRIENT_IDS["calories"]),
        "protein_g": _extract_nutrient(nutrients, NUTRIENT_IDS["protein_g"]),
        "fat_g": _extract_nutrient(nutrients, NUTRIENT_IDS["fat_g"]),
        "carbs_g": _extract_nutrient(nutrients, NUTRIENT_IDS["carbs_g"]),
        "fiber_g": _extract_nutrient(nutrients, NUTRIENT_IDS["fiber_g"]),
        "serving_size": f"{raw.get('servingSize', 100)}{raw.get('servingSizeUnit', 'g')}",
    }


def search_foods(query: str, page_size: int = 10) -> list[dict]:
    resp = httpx.get(
        f"{USDA_BASE_URL}/foods/search",
        params={"api_key": USDA_API_KEY, "query": query, "pageSize": page_size,
                "dataType": "Foundation,SR Legacy"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return [parse_food(f) for f in data.get("foods", [])]
