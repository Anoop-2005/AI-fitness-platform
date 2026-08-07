"""
Goal prediction endpoints.
GET /api/goal/prediction — get user's goal prediction
"""
from fastapi import APIRouter, Depends

from db import get_db
from auth import get_current_user
from services.goal_prediction import compute_goal_prediction

router = APIRouter(prefix="/api/goal", tags=["goal"])


@router.get("/prediction")
def get_goal_prediction(user=Depends(get_current_user), db=Depends(get_db)):
    """Get goal prediction for the current user."""
    prediction = compute_goal_prediction(db, user["id"])

    if "error" in prediction:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=prediction["error"])

    return prediction
