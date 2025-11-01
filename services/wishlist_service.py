import uuid
from typing import List
from fastapi import HTTPException
from datetime import datetime
from google.cloud.firestore import FieldFilter

# Import our centralized configs and services
from .firebase_config import db
from firebase_admin import firestore

async def add_to_wishlist(user_id: str, product_id: str) -> dict:
    """
    Adds a product to a user's wishlist.
    If the product is already in the wishlist, returns the existing entry.
    Creates a new wishlist entry with a unique wishlist_id only if it doesn't exist.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # Check if this user already has this product in their wishlist
        existing_wishlists = db.collection("wishlists").where(filter=FieldFilter("user_id", "==", user_id)).where(filter=FieldFilter("product_id", "==", product_id)).limit(1).stream()

        # If it exists, return the existing entry
        for doc in existing_wishlists:
            existing_data = doc.to_dict()
            # Convert timestamp to ISO format if it's a Firestore timestamp
            if isinstance(existing_data.get('timestamp'), datetime):
                existing_data['timestamp'] = existing_data['timestamp'].isoformat()
            return existing_data

        # If not exists, create new entry
        wishlist_id = str(uuid.uuid4())

        wishlist_data = {
            "wishlist_id": wishlist_id,
            "user_id": user_id,
            "product_id": product_id,
            "timestamp": firestore.SERVER_TIMESTAMP
        }

        # Store in wishlists collection with wishlist_id as document ID
        db.collection("wishlists").document(wishlist_id).set(wishlist_data)

        return {
            "wishlist_id": wishlist_id,
            "user_id": user_id,
            "product_id": product_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add to wishlist: {str(e)}")

async def get_user_wishlist(user_id: str) -> dict:
    """
    Retrieves all wishlist items for a specific user.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # Query wishlists collection for items by this user
        wishlists_ref = db.collection("wishlists").where(filter=FieldFilter("user_id", "==", user_id))
        wishlists_docs = wishlists_ref.stream()

        wishlist_items = []
        for doc in wishlists_docs:
            item_data = doc.to_dict()
            # Convert timestamp to ISO format if it's a Firestore timestamp
            if isinstance(item_data.get('timestamp'), datetime):
                item_data['timestamp'] = item_data['timestamp'].isoformat()
            wishlist_items.append(item_data)

        return {
            "user_id": user_id,
            "total_items": len(wishlist_items),
            "wishlist_items": wishlist_items
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user wishlist: {str(e)}")

async def get_product_wishlist(product_id: str) -> dict:
    """
    Retrieves all wishlist entries for a specific product.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # Query wishlists collection for items with this product_id
        wishlists_ref = db.collection("wishlists").where(filter=FieldFilter("product_id", "==", product_id))
        wishlists_docs = wishlists_ref.stream()

        wishlist_entries = []
        for doc in wishlists_docs:
            entry_data = doc.to_dict()
            # Convert timestamp to ISO format if it's a Firestore timestamp
            if isinstance(entry_data.get('timestamp'), datetime):
                entry_data['timestamp'] = entry_data['timestamp'].isoformat()
            wishlist_entries.append(entry_data)

        return {
            "product_id": product_id,
            "total_likes": len(wishlist_entries),
            "wishlist_entries": wishlist_entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve product wishlist: {str(e)}")

async def delete_wishlist_item(wishlist_id: str) -> dict:
    """
    Deletes a wishlist item by its wishlist_id.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        wishlist_ref = db.collection("wishlists").document(wishlist_id)
        doc = wishlist_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail=f"Wishlist item with id {wishlist_id} not found.")

        # Get the data before deleting for response
        wishlist_data = doc.to_dict()

        # Delete the document
        wishlist_ref.delete()

        return {
            "message": "Wishlist item deleted successfully",
            "wishlist_id": wishlist_id,
            "user_id": wishlist_data.get('user_id'),
            "product_id": wishlist_data.get('product_id')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete wishlist item: {str(e)}")

async def get_artisan_wishlist(user_id: str) -> dict:
    """
    Retrieves all wishlist entries where the artisan's products are wishlisted.
    This gets all wishlist items for all products belonging to this artisan.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # First, get all product_ids for this artisan
        products_ref = db.collection("product_stories").document(user_id).collection("products")
        products_docs = products_ref.stream()

        product_ids = [doc.id for doc in products_docs]

        if not product_ids:
            return {
                "user_id": user_id,
                "total_entries": 0,
                "wishlist_entries": []
            }

        # Now get all wishlist entries for these product_ids
        wishlist_entries = []
        for product_id in product_ids:
            product_wishlist = await get_product_wishlist(product_id)
            wishlist_entries.extend(product_wishlist["wishlist_entries"])

        return {
            "user_id": user_id,
            "total_entries": len(wishlist_entries),
            "wishlist_entries": wishlist_entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve artisan wishlist: {str(e)}")