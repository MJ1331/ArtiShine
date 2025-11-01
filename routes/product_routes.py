# routes/product_routes.py
from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Depends, Body
from typing import List
from services import product_service, user_service

router = APIRouter()

@router.post("/create-product",
    summary="Create a New Product and Trigger Post",
    description="This endpoint uploads product media, generates a story via AI, and posts it to Instagram."
)
async def create_product_endpoint(
    current_user: dict = Depends(user_service.get_current_user),
    images: List[UploadFile] = File(..., description="1 to 4 product images"),
    voice_file: UploadFile = File(..., description="A single voice file describing the product")
):
    """
    Creates a new product for the authenticated user. You must provide:
    - `images`: Between 1 and 4 image files.
    - `voice_file`: A single audio file (e.g., .wav, .mp3).

    This triggers the full workflow: STT -> Translate -> Story Gen -> Insta Post.
    """
    if not 1 <= len(images) <= 4:
        raise HTTPException(status_code=400, detail="You must upload between 1 and 4 images.")

    user_id = current_user["user_id"]
    return await product_service.create_new_product(user_id, images, voice_file)

@router.get("/",
    summary="Get All Products",
    description="Retrieves all products from all artisans with their complete details."
)
async def get_all_products_endpoint():
    """
    Returns all products with their details and associated user_id.
    """
    return await product_service.get_all_products()

@router.get("/my-products",
    summary="Get My Products",
    description="Retrieves all products for the authenticated artisan user."
)
async def get_my_products_endpoint(current_user: dict = Depends(user_service.get_current_user)):
    """
    Returns all products for the authenticated user with their details.
    """
    user_id = current_user["user_id"]

@router.get("/{user_id}/products",
    summary="Get All Products by User ID",
    description="Retrieves all products for a specific artisan using their user ID."
)
async def get_products_by_user_id_endpoint(user_id: str):
    """
    Returns all products for the specified user_id with their details.
    """
    return await product_service.get_products_by_user_id(user_id)

@router.get("/{product_id}",
    summary="Get Product Details by Product ID",
    description="Retrieves detailed information for a specific product by its product ID."
)
async def get_product_details_endpoint(product_id: str):
    """
    Returns detailed information for the specified product_id.
    """
    return await product_service.get_product_details_by_id(product_id)

@router.delete("/{user_id}/products/{product_id}",
    summary="Delete a Product by Product ID",
    description="Deletes a specific product for an artisan using their user ID and the product ID."
)
async def delete_product_route(user_id: str, product_id: str):
    return await product_service.delete_product(user_id, product_id)

@router.patch("/{user_id}/products/{product_id}",
    summary="Partially Update a Product by Product ID",
    description="Partially updates a specific product for an artisan using their user ID and the product ID."
)
async def patch_product_route(user_id: str, product_id: str, payload: dict = Body(...)):
    return await product_service.update_product_partially(user_id, product_id, payload)