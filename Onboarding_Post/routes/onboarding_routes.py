# routes/onboarding_routes.py

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict
from services.onboarding_service import OnboardingService

router = APIRouter()

# --- Pydantic Models for Request and Response ---
class ArtisanID(BaseModel):
    UserID: str = Field(..., description="The unique identifier for the artisan.")

class OnboardingOutput(BaseModel):
    UserID: str
    CaptionData: Dict
    ImageURL: str

# --- API Endpoint ---
@router.post(
    "/generate-post", 
    response_model=OnboardingOutput,
    tags=["Onboarding"]
)
async def create_onboarding_post_endpoint(
    details: ArtisanID, 
    service: OnboardingService = Depends()
):
    """
    This endpoint takes a UserID and orchestrates the generation of an
    onboarding post by calling the onboarding service.
    """
    return await service.create_onboarding_post(details)