# routes/map_explore_routes.py
from fastapi import APIRouter
from services import product_service

router = APIRouter()

@router.get("/artisans",
    summary="Get All Artisans with Details and Product Images",
    description="Retrieves all artisans with their location details (place, latitude, longitude) and all their product images."
)
async def get_all_artisans_with_images():
    """
    Returns all artisans with their details and all product images for each artisan.
    """
    return await product_service.get_all_artisans_with_images()