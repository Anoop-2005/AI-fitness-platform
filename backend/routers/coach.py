from fastapi import APIRouter, Depends
from pydantic import BaseModel
from db import get_db
from auth import get_current_user
from services.coach_service import get_coach_response

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