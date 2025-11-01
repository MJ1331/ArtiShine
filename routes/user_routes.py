# routes/user_routes.py
from fastapi import APIRouter, Depends, Form, Body, HTTPException, UploadFile, File
from services import user_service
from models.user_models import ArtisanDetails, BuyerDetails, LoginRequest # Import the models
from typing import Dict, Any

router = APIRouter()

@router.post("/register",
    summary="Register a New Artisan and Trigger Onboarding",
    description="This single endpoint registers a new user, generates their onboarding post, and posts it to Instagram."
)
async def register_artisan_endpoint(details: ArtisanDetails):
    """
    Registers a new artisan. The request body must contain all artisan details.
    This will automatically trigger the full onboarding workflow.
    """
    return await user_service.register_artisan(details)

@router.get("/",
    summary="Get All Registered Artisans",
    description="Retrieves a list of all artisans registered in the system with their complete details."
)
async def get_all_artisans_endpoint():
    """
    Returns all registered artisans with their user_id and all stored information.
    """
    return await user_service.get_all_artisans()

@router.get("/me",
    summary="Get My Profile",
    description="Retrieves the complete details of the authenticated artisan."
)
async def get_my_profile_endpoint(current_user: dict = Depends(user_service.get_current_user)):
    """
    Returns the authenticated artisan's details.
    """
    # Check if the user is an artisan
    if current_user.get("role") != "artisan":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied. Artisan role required.")

    user_id = current_user["user_id"]
    return await user_service.get_artisan_by_id(user_id)

@router.post("/login",
    summary="Login User",
    description="Authenticates a user (artisan or buyer) using email, password, and role, returns a JWT token."
)
async def login_user_endpoint(login_data: LoginRequest):
    """
    Authenticates the user and returns a JWT token for subsequent requests.
    """
    return await user_service.login_user(login_data)

@router.post("/register-buyer",
    summary="Register a New Buyer",
    description="Registers a new buyer with their basic information."
)
async def register_buyer_endpoint(details: BuyerDetails):
    """
    Registers a new buyer. The request body must contain buyer details.
    """
    return await user_service.register_buyer(details)

@router.get("/buyers",
    summary="Get All Registered Buyers",
    description="Retrieves a list of all buyers registered in the system with their complete details."
)
async def get_all_buyers_endpoint():
    """
    Returns all registered buyers with their user_id and all stored information.
    """
    return await user_service.get_all_buyers()

@router.get("/buyers/{user_id}",
    summary="Get Buyer by User ID",
    description="Retrieves the complete details of a specific buyer by their user ID."
)
async def get_buyer_by_id_endpoint(user_id: str):
    """
    Returns the buyer's details for the specified user_id.
    """
    return await user_service.get_buyer_by_id(user_id)

@router.get("/profile/{user_id}",
    summary="Get User Profile with Products",
    description="Retrieves a user's complete profile along with all their products (if artisan)."
)
async def get_user_profile_with_products_endpoint(user_id: str):
    """
    Returns user details and their products for the specified user_id.
    Works for both artisans (with products) and buyers.
    """
    return await user_service.get_user_with_products(user_id)

@router.get("/buyers/me",
    summary="Get My Buyer Profile",
    description="Retrieves the complete details of the authenticated buyer."
)
async def get_my_buyer_profile_endpoint(current_user: dict = Depends(user_service.get_current_user)):
    """
    Returns the authenticated buyer's details.
    """
    # Check if the user is a buyer
    if current_user.get("role") != "buyer":
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Access denied. Buyer role required.")

    user_id = current_user["user_id"]

@router.patch(
    "/me",
    summary="Update artisan profile (unprotected)",
    description="Unprotected: include user_id in JSON body along with fields to update (name, shopName, location, bio, phone, typeOfWork)."
)
async def patch_users_me(payload: Dict[str, Any] = Body(...)):
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Invalid JSON body; expected an object.")

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required in request body.")

    # Build updates dict (only include recognized frontend keys)
    allowed_keys = {"name", "shopName", "location", "bio", "phone", "typeOfWork"}
    updates = {k: v for k, v in payload.items() if k in allowed_keys}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update. Allowed: name, shopName, location, bio, phone, typeOfWork")

    return await user_service.update_artisan_profile_unprotected(user_id=user_id, updates=updates)


# --------------------------------------------------------------
# UNPROTECTED: POST /users/me/photo
# Accepts form-data user_id (string) and file (image)
# --------------------------------------------------------------
@router.post(
    "/me/photo",
    summary="Upload profile photo (unprotected)",
    description="Unprotected: form-data with user_id and file (image)."
)
async def post_users_me_photo(user_id: str = Form(...), file: UploadFile = File(...)):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id form field is required.")
    if not file:
        raise HTTPException(status_code=400, detail="file is required.")
    return await user_service.upload_profile_photo_unprotected(user_id=user_id, file=file)
