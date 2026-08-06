from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from db import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/photos", tags=["photos"])


class PhotoUploadRequest(BaseModel):
    view_type: str  # "front", "side", "back"
    image_data: str  # base64 encoded image


class PhotoResponse(BaseModel):
    id: int
    user_id: str
    view_type: str
    photo_url: str
    uploaded_at: str


@router.post("/upload")
def upload_photo(
    body: PhotoUploadRequest,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Store photo metadata. Image itself goes to Supabase Storage from frontend."""
    if body.view_type not in ("front", "side", "back"):
        raise HTTPException(status_code=400, detail="view_type must be 'front', 'side', or 'back'")

    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO progress_photos (user_id, view_type, photo_url, uploaded_at)
            VALUES (%s, %s, %s, NOW())
            RETURNING id, user_id, view_type, photo_url, uploaded_at
        """, (user["id"], body.view_type, body.image_data))
        row = cur.fetchone()
    return row


@router.get("/list")
def list_photos(
    view_type: Optional[str] = None,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """List user's progress photos, optionally filtered by view_type."""
    query = "SELECT * FROM progress_photos WHERE user_id = %s"
    params = [user["id"]]

    if view_type:
        query += " AND view_type = %s"
        params.append(view_type)

    query += " ORDER BY uploaded_at DESC"

    with db.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


@router.get("/latest")
def get_latest_photos(user=Depends(get_current_user), db=Depends(get_db)):
    """Get the most recent photo for each view type."""
    with db.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (view_type) *
            FROM progress_photos
            WHERE user_id = %s
            ORDER BY view_type, uploaded_at DESC
        """, (user["id"],))
        return cur.fetchall()


@router.delete("/{photo_id}")
def delete_photo(
    photo_id: int,
    user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Delete a progress photo."""
    with db.cursor() as cur:
        cur.execute(
            "DELETE FROM progress_photos WHERE id = %s AND user_id = %s RETURNING id",
            (photo_id, user["id"])
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Photo not found")
    return {"success": True}