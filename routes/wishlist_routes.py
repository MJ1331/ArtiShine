# routes/wishlist_routes.py
from fastapi import APIRouter, HTTPException, Depends
from services import wishlist_service, user_service
from models.wishlist_models import WishlistCreate

router = APIRouter()

@router.post("/{user_id}",
    summary="Add Product to Wishlist",
    description="Adds a product to a user's wishlist by user_id."
)
async def add_to_wishlist_endpoint(
    user_id: str,
    wishlist_item: WishlistCreate
):
    """
    Adds a product to the specified user's wishlist.
    No authentication required.
    """
    return await wishlist_service.add_to_wishlist(user_id, wishlist_item.product_id)

@router.get("/{user_id}",
    summary="Get User Wishlist",
    description="Retrieves all wishlist items for a user by user_id."
)
async def get_user_wishlist_endpoint(user_id: str):
    """
    Returns all products in the specified user's wishlist.
    No authentication required.
    """
    return await wishlist_service.get_user_wishlist(user_id)

@router.get("/user/{user_id}",
    summary="Get User Wishlist",
    description="Retrieves all wishlist items for a specific user."
)
async def get_user_wishlist_endpoint(user_id: str):
    """
    Returns all products in the specified user's wishlist.
    """
    return await wishlist_service.get_user_wishlist(user_id)

@router.get("/product/{product_id}",
    summary="Get Product Wishlist Entries",
    description="Retrieves all wishlist entries for a specific product."
)
async def get_product_wishlist_endpoint(product_id: str):
    """
    Returns all wishlist entries (likes) for the specified product.
    """
    return await wishlist_service.get_product_wishlist(product_id)

@router.delete("/{wishlist_id}",
    summary="Delete Wishlist Item",
    description="Deletes a wishlist item by its wishlist_id."
)
async def delete_wishlist_item_endpoint(wishlist_id: str):
    """
    Deletes the specified wishlist item.
    """
    return await wishlist_service.delete_wishlist_item(wishlist_id)

@router.get("/artisan/{user_id}",
    summary="Get Artisan Wishlist Entries",
    description="Retrieves all wishlist entries for all products belonging to an artisan."
)
async def get_artisan_wishlist_endpoint(user_id: str):
    """
    Returns all wishlist entries for products created by the specified artisan.
    """
    return await wishlist_service.get_artisan_wishlist(user_id)