# services/user_service.py
import uuid
from fastapi import HTTPException
from .firebase_config import db
from . import onboarding_service
from models.user_models import ArtisanDetails

async def register_artisan(details: ArtisanDetails):
    """
    1. Creates a new artisan in Firestore.
    2. Triggers the onboarding post generation and posting.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # Generate a new unique UserID
        user_id = str(uuid.uuid4())
        
        # Store user details in 'artisans' collection
        artisan_ref = db.collection("artisans").document(user_id)
        artisan_ref.set(details.dict())
        print(f"Artisan {user_id} created in Firestore.")

        # --- WORKFLOW STEP 2: Trigger Onboarding ---
        # This function will generate the post, save it, AND post it
        print(f"Triggering onboarding process for {user_id}...")
        onboarding_data = await onboarding_service.generate_and_post_onboarding(user_id)
        
        return {
            "message": "Artisan registered and onboarding post created.",
            "user_id": user_id,
            "onboarding_post_details": onboarding_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")