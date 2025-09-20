# routes/insta_product_routes.py

from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from typing import List

# Import the service functions that contain the core logic
from services.insta_product_service import get_product_story, format_story_caption, post_story_to_instagram

# --- API Router Definition ---
router = APIRouter()

@router.post("/post_product_story/", tags=["Product Story"])
async def create_product_post_endpoint(
    user_id: str = Form(...),
    product_id: str = Form(...),
    images: List[UploadFile] = File(...)
):
    """
    Creates an Instagram post from product story data and uploaded images.
    - **user_id**: The ID of the artisan.
    - **product_id**: The ID of the product.
    - **images**: 1 to 5 image files to be uploaded.
    """
    # 1. Validate Input
    if not 0 < len(images) <= 5:
        raise HTTPException(
            status_code=400, 
            detail="You must upload between 1 and 5 images."
        )

    # 2. Fetch Story Data from Firestore
    story_data = get_product_story(user_id, product_id)
    if not story_data:
        raise HTTPException(
            status_code=404,
            detail=f"Product story not found for UserID '{user_id}' and ProductID '{product_id}'"
        )

    # 3. Format the Caption
    caption = format_story_caption(story_data)

    # 4. Post to Instagram
    success = await post_story_to_instagram(caption, images)
    if not success:
        raise HTTPException(
            status_code=500, 
            detail="Failed to post to Instagram. Check server logs for details."
        )

    # 5. Return Success Response
    return {"message": f"Successfully posted product story for ProductID: {product_id}"}