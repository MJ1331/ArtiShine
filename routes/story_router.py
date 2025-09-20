# routes/story_router.py
# --- MODIFIED ---

import base64
import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from services.story_services import generate_story_from_details, save_story_to_gcs_and_firestore
from firebase_admin import firestore

# --- Router Setup ---
router = APIRouter()
db = firestore.client()

@router.post("/generate-story/", tags=["Story Generation"])
async def generate_story_endpoint(
    user_id: str = Form(...),
    product_id: str = Form(...),
    images: List[UploadFile] = File(...)
):
    """
    Generates a story by fetching artisan details and audio transcript from Firestore,
    and combining them with uploaded product images.
    """
    if len(images) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images allowed")

    # 1. Fetch Artisan Details from 'artisans' collection
    artisan_ref = db.collection("artisans").document(user_id)
    artisan_doc = artisan_ref.get()
    if not artisan_doc.exists:
        raise HTTPException(status_code=404, detail=f"Artisan with user_id '{user_id}' not found.")
    
    artisan_data = artisan_doc.to_dict()
    name = artisan_data.get("name")
    shop_name = artisan_data.get("shop_name")
    location = artisan_data.get("location")
    if not all([name, shop_name, location]):
        raise HTTPException(status_code=400, detail=f"Artisan document for '{user_id}' is missing required fields (name, shop_name, location).")

    # 2. Fetch Audio Transcript from 'translations' sub-collection
    transcript_ref = db.collection("translations").document(user_id).collection("users").document(product_id)
    transcript_doc = transcript_ref.get()
    if not transcript_doc.exists:
        raise HTTPException(status_code=404, detail=f"Transcript for product_id '{product_id}' not found for the given user.")
    
    transcript_data = transcript_doc.to_dict()
    audio_transcript = transcript_data.get("translatedText")
    if not audio_transcript:
        raise HTTPException(status_code=400, detail=f"Transcript document for product_id '{product_id}' is missing the 'translatedText' field.")

    # 3. Process Images
    base64_images = []
    for image_file in images:
        image_bytes = await image_file.read()
        base64_images.append(base64.b64encode(image_bytes).decode("utf-8"))

    # 4. Call the Story Generation Service with all fetched details
    details_dict = {
        "audio_transcript": audio_transcript,
        "name": name,
        "shop_name": shop_name,
        "location": location,
        "base64_images": base64_images
    }
    story_content = generate_story_from_details(details_dict)
    if "error" in story_content:
        raise HTTPException(status_code=500, detail=f"Failed to generate story: {story_content['error']}")

    # 5. Assemble and Save Final Data
    final_data = {
        "user_id": user_id,
        "product_id": product_id,
        "name": name,
        "shop_name": shop_name,
        "location": location,
        "story": story_content,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    save_story_to_gcs_and_firestore(final_data)

    # 6. Return Response
    return JSONResponse(content=final_data)