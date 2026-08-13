
from fastapi import APIRouter, Depends

from db import get_db
from auth import get_current_user
from services.body_composition import analyze_body_composition

router = APIRouter(prefix="/api/body-composition", tags=["body-composition"])


@router.get("/insights")
def get_insights(user=Depends(get_current_user), db=Depends(get_db)):
    """Get body composition insights for the current user."""
    result = analyze_body_composition(db, user["id"])
    return result