from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from firebase_admin import firestore
from utils.dependencies import get_current_buyer
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
db = firestore.client()

class GeoQuery(BaseModel):
    lat: float
    lon: float
    radius_km: float = 10.0

@router.get("/products-in-radius")
async def get_products_in_radius(query: GeoQuery = Depends()):
    try:
        # Placeholder for GeoFirestore or geohashing implementation
        # Query artisans within radius
        artisans = db.collection('users').where('role', '==', 'artisan').get()  # Simplified
        artisan_ids = [artisan.id for artisan in artisans]
        
        # Query products for these artisans
        products = db.collection('products').where('artisanId', 'in', artisan_ids).get()
        product_list = [doc.to_dict() for doc in products]
        
        return {"products": product_list}
    except Exception as e:
        logger.error(f"Products in radius error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/artisans-in-radius")
async def get_artisans_in_radius(query: GeoQuery = Depends()):
    try:
        # Placeholder for GeoFirestore or geohashing implementation
        artisans = db.collection('users').where('role', '==', 'artisan').get()  # Simplified
        artisan_list = [
            {
                "userId": artisan.id,
                "name": artisan.to_dict().get("name"),
                "shopName": artisan.to_dict().get("shopName"),
                "location": artisan.to_dict().get("location", {})
            }
            for artisan in artisans
        ]
        return {"artisans": artisan_list}
    except Exception as e:
        logger.error(f"Artisans in radius error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/me/wishlist")
async def update_wishlist(
    productId: str,
    action: str,
    current_buyer: tuple = Depends(get_current_buyer)
):
    user_data, uid = current_buyer
    try:
        if action not in ["add", "remove"]:
            raise HTTPException(status_code=400, detail="Invalid action. Must be 'add' or 'remove'")
        
        if action == "add":
            db.collection('users').document(uid).update({
                'wishlist': firestore.ArrayUnion([productId])
            })
        else:
            db.collection('users').document(uid).update({
                'wishlist': firestore.ArrayRemove([productId])
            })
        
        return {"message": "Wishlist updated"}
    except Exception as e:
        logger.error(f"Wishlist update error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/me/wishlist")
async def get_wishlist(current_buyer: tuple = Depends(get_current_buyer)):
    user_data, uid = current_buyer
    try:
        user_doc = db.collection('users').document(uid).get()
        wishlist = user_doc.to_dict().get('wishlist', [])
        products = db.collection('products').where('productId', 'in', wishlist).get()
        product_list = [doc.to_dict() for doc in products]
        return {"products": product_list}
    except Exception as e:
        logger.error(f"Get wishlist error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")