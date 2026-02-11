from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fatsecret_api import search_food, get_food_details

app = FastAPI(title="Food Calorie & Macro Tracker API")


class FoodRequest(BaseModel):
    food_id: str
    quantity: float
    unit: str  # "serving" or "grams"


@app.get("/")
def root():
    return {"status": "API is running"}


@app.get("/search")
def search(query: str):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    foods = search_food(query)

    unique = {}
    for food in foods:
        key = food["food_name"].lower()
        if key not in unique:
            unique[key] = {
                "food_id": food["food_id"],
                "food_name": food["food_name"]
            }

    return list(unique.values())


@app.post("/details")
def food_details(req: FoodRequest):
    if req.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")

    details = get_food_details(req.food_id)

    servings = details["servings"]["serving"]
    serving = servings[0] if isinstance(servings, list) else servings

    calories = float(serving.get("calories", 0))
    carbs = float(serving.get("carbohydrate", 0))
    protein = float(serving.get("protein", 0))
    fat = float(serving.get("fat", 0))

    multiplier = 1.0

    if req.unit == "serving":
        multiplier = req.quantity

    elif req.unit == "grams":
        grams_per_serving = float(serving.get("metric_serving_amount", 0))
        if grams_per_serving <= 0:
            raise HTTPException(status_code=400, detail="Gram data not available")
        multiplier = req.quantity / grams_per_serving

    else:
        raise HTTPException(status_code=400, detail="Invalid unit")

    return {
        "food_name": details["food_name"],
        "quantity": f"{req.quantity} {req.unit}",
        "calories": round(calories * multiplier, 2),
        "carbs": round(carbs * multiplier, 2),
        "protein": round(protein * multiplier, 2),
        "fat": round(fat * multiplier, 2),
    }
