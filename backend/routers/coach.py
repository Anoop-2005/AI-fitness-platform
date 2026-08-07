from fastapi import APIRouter, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user
from services.coach_service import get_coach_response
from services.enrichment import generate_motivational_message

router = APIRouter(prefix="/api/coach", tags=["coach"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("/chat")
def coach_chat(
    body: ChatRequest,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    reply = get_coach_response(db, user["id"], body.message)
    return {"reply": reply}


@router.get("/motivation")
def get_motivation(user=Depends(get_current_user), db=Depends(get_db)):
    """Get a personalized motivational message for the user."""
    from services.profile_helpers import get_profile

    profile = get_profile(db, user["id"])
    user_name = profile.get("full_name", "User").split(" ")[0] if profile else "User"
    goal = profile.get("primary_goal", "fitness") if profile else "fitness"

    # Calculate streak
    from datetime import date, timedelta
    streak = 0
    with db.cursor() as cur:
        cur.execute("""
            SELECT log_date FROM habit_logs
            WHERE user_id = %s AND workout_done = TRUE
            ORDER BY log_date DESC
        """, (user["id"],))
        workout_dates = cur.fetchone()
        if workout_dates:
            # Simple streak calc
            check_date = date.today()
            while True:
                cur.execute("SELECT 1 FROM habit_logs WHERE user_id = %s AND log_date = %s AND workout_done = TRUE", (user["id"], check_date))
                if cur.fetchone():
                    streak += 1
                    check_date -= timedelta(days=1)
                else:
                    break

    # Calculate adherence (simplified)
    adherence = 75.0  # Default

    message = generate_motivational_message(user_name, streak, goal, adherence)
    return {"message": message, "streak": streak, "goal": goal}