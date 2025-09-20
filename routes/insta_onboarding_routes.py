# routes/insta_onboarding_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
# UPDATED: Import from the new service filename
from services.insta_onboarding_service import get_onboarding_post, post_to_instagram

# --- Pydantic model ---
class OnboardingRequest(BaseModel):
    user_id: str

# --- API Router Definition ---
router = APIRouter()

@router.post("/post_onboarding")
async def create_onboarding_post(request_data: OnboardingRequest):
    post_document = get_onboarding_post(request_data.user_id)
    
    if not post_document:
        raise HTTPException(
            status_code=404,
            detail=f"Onboarding post not found for UserID: {request_data.user_id}"
        )

    success = post_to_instagram(post_document)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to post to Instagram. Check server logs for details."
        )

    return {"message": f"Successfully posted onboarding for UserID: {request_data.user_id}"}