# routes/product_routes.py
from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from typing import List
from services import product_service

router = APIRouter()

@router.post("/create-product",
    summary="Create a New Product and Trigger Post",
    description="This endpoint uploads product media, generates a story via AI, and posts it to Instagram."
)
async def create_product_endpoint(
    user_id: str = Form(..., description="The UserID of the artisan"),
    images: List[UploadFile] = File(..., description="1 to 4 product images"),
    voice_file: UploadFile = File(..., description="A single voice file describing the product")
):
    """
    Creates a new product. You must provide:
    - `user_id`: The artisan's unique ID.
    - `images`: Between 1 and 4 image files.
    - `voice_file`: A single audio file (e.g., .wav, .mp3).
    
    This triggers the full workflow: STT -> Translate -> Story Gen -> Insta Post.
    """
    if not 1 <= len(images) <= 4:
        raise HTTPException(status_code=400, detail="You must upload between 1 and 4 images.")
    
    return await product_service.create_new_product(user_id, images, voice_file)