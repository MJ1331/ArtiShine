# models/wishlist_models.py
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class WishlistItem(BaseModel):
    wishlist_id: str = Field(..., description="Unique ID for the wishlist entry")
    user_id: str = Field(..., description="ID of the user who added to wishlist")
    product_id: str = Field(..., description="ID of the product added to wishlist")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the item was added")

class WishlistCreate(BaseModel):
    product_id: str = Field(..., description="ID of the product to add to wishlist")

class WishlistResponse(BaseModel):
    wishlist_id: str
    user_id: str
    product_id: str
    timestamp: datetime

class UserWishlistResponse(BaseModel):
    user_id: str
    total_items: int
    wishlist_items: List[WishlistResponse]

class ProductWishlistResponse(BaseModel):
    product_id: str
    total_likes: int
    wishlist_entries: List[WishlistResponse]