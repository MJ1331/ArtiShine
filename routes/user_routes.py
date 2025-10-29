# routes/user_routes.py
from fastapi import APIRouter
from services import user_service
from models.user_models import ArtisanDetails # Import the model

router = APIRouter()

@router.post("/register",
    summary="Register a New Artisan and Trigger Onboarding",
    description="This single endpoint registers a new user, generates their onboarding post, and posts it to Instagram."
)
async def register_artisan_endpoint(details: ArtisanDetails):
    """
    Registers a new artisan. The request body must contain all artisan details.
    This will automatically trigger the full onboarding workflow.
    """
    return await user_service.register_artisan(details)