# services/user_service.py
import uuid
import bcrypt
import jwt
from fastapi import HTTPException, Depends, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .firebase_config import db
from . import onboarding_service
from models.user_models import ArtisanDetails, BuyerDetails, LoginRequest, UserRole
from dotenv import load_dotenv
import os

# NEW imports for uploads / timestamps
from fastapi import UploadFile
from firebase_admin import storage
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import unquote

# -------------------------- Helper function for blob name parsing --------------------------
def _get_blob_name_from_url(url: str) -> Optional[str]:
    """
    Extracts the correct blob name from a GCS public URL.
    Handles URL encoding (e.g., %20, %2520 → space).
    """
    if not url or not bucket:
        return None

    bucket_name = bucket.name
    public_prefix = f"https://storage.googleapis.com/{bucket_name}/"
    if url.startswith(public_prefix):
        encoded_path = url[len(public_prefix):]
        return unquote(encoded_path)

    # Fallback for gs:// URLs
    gs_prefix = f"gs://{bucket_name}/"
    if url.startswith(gs_prefix):
        encoded_path = url[len(gs_prefix):]
        return unquote(encoded_path)

    # Last-ditch fallback
    try:
        parts = url.split(f"/{bucket_name}/", 1)
        if len(parts) > 1:
            return unquote(parts[1])
    except:
        pass

    return None

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
security = HTTPBearer()

async def register_artisan(details: ArtisanDetails):
    """
    1. Creates a new artisan in Firestore with hashed password.
    2. Triggers the onboarding post generation and posting.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # Check if email already exists in artisans collection
        from google.cloud.firestore import FieldFilter
        existing_artisan = db.collection("artisans").where(filter=FieldFilter("email", "==", details.email)).limit(1).stream()
        if any(existing_artisan):
            raise HTTPException(status_code=409, detail="Email already registered as artisan.")
        
        # Check if email exists in buyers collection
        existing_buyer = db.collection("buyers").where(filter=FieldFilter("email", "==", details.email)).limit(1).stream()
        if any(existing_buyer):
            raise HTTPException(status_code=409, detail="Email already registered as buyer.")

        # Generate a new unique UserID
        user_id = str(uuid.uuid4())

        # Hash the password
        hashed_password = bcrypt.hashpw(details.password.encode('utf-8'), bcrypt.gensalt())

        # Prepare artisan data (exclude plain password)
        artisan_data = details.dict()
        artisan_data['password_hash'] = hashed_password.decode('utf-8')
        del artisan_data['password']  # Remove plain password

        # Store user details in 'artisans' collection
        artisan_ref = db.collection("artisans").document(user_id)
        artisan_ref.set(artisan_data)
        print(f"Artisan {user_id} created in Firestore.")

        # --- WORKFLOW STEP 2: Trigger Onboarding ---
        # This function will generate the post, save it, AND post it
        print(f"Triggering onboarding process for {user_id}...")
        onboarding_data = await onboarding_service.generate_and_post_onboarding(user_id)

        return {
            "message": "Artisan registered and onboarding post created.",
            "user_id": user_id,
            "onboarding_post_details": onboarding_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

async def get_all_artisans():
    """
    Retrieves all registered artisans from Firestore.
    Returns a list of artisans with their user_id and all details.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        artisans_ref = db.collection("artisans")
        docs = artisans_ref.stream()

        artisans = []
        for doc in docs:
            artisan_data = doc.to_dict()
            artisan_data["user_id"] = doc.id  # Include the document ID as user_id
            artisans.append(artisan_data)

        return {
            "total_artisans": len(artisans),
            "artisans": artisans
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve artisans: {str(e)}")

async def get_artisan_by_id(user_id: str):
    """
    Retrieves a specific artisan by their user_id from Firestore.
    Returns the artisan's details if found.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        artisan_ref = db.collection("artisans").document(user_id)
        doc = artisan_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Artisan not found.")

        artisan_data = doc.to_dict()
        artisan_data["user_id"] = doc.id  # Include the document ID as user_id

        return artisan_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve artisan: {str(e)}")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency function to get the current authenticated user from JWT token.
    Returns user info including role for role-based operations.
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])

        user_id = payload.get("user_id")
        email = payload.get("email")
        role = payload.get("role")

        if not user_id or not email or not role:
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        return {"user_id": user_id, "email": email, "role": role}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token.")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

async def login_user(login_data: LoginRequest):
    """
    Authenticates a user (artisan or buyer) using email, password, and role.
    Returns a JWT token if authentication is successful.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # Determine collection based on role
        collection_name = "artisans" if login_data.role == UserRole.ARTISAN else "buyers"

        # Find user by email in the appropriate collection
        users_ref = db.collection(collection_name)
        from google.cloud.firestore import FieldFilter
        query = users_ref.where(filter=FieldFilter("email", "==", login_data.email)).limit(1)
        docs = query.stream()

        user_doc = None
        user_id = None
        for doc in docs:
            user_doc = doc
            user_id = doc.id
            break

        if not user_doc:
            raise HTTPException(status_code=401, detail="Invalid email, password, or role.")

        user_data = user_doc.to_dict()

        # Verify password
        stored_hash = user_data.get("password_hash")
        if not stored_hash:
            raise HTTPException(status_code=401, detail="Invalid email, password, or role.")

        if not bcrypt.checkpw(login_data.password.encode('utf-8'), stored_hash.encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid email, password, or role.")

        # Generate JWT token
        payload = {
            "user_id": user_id,
            "email": login_data.email,
            "role": login_data.role.value,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24)  # Token expires in 24 hours
        }

        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

        return {
            "message": "Login successful.",
            "user_id": user_id,
            "role": login_data.role.value,
            "token": token,
            "token_type": "bearer"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

async def register_buyer(details: BuyerDetails):
    """
    Registers a new buyer in Firestore with hashed password.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # Check if email already exists in buyers collection
        from google.cloud.firestore import FieldFilter
        existing_buyer = db.collection("buyers").where(filter=FieldFilter("email", "==", details.email)).limit(1).stream()
        if any(existing_buyer):
            raise HTTPException(status_code=409, detail="Email already registered as buyer.")
        
        # Check if email exists in artisans collection
        existing_artisan = db.collection("artisans").where(filter=FieldFilter("email", "==", details.email)).limit(1).stream()
        if any(existing_artisan):
            raise HTTPException(status_code=409, detail="Email already registered as artisan.")

        # Generate a new unique UserID
        user_id = str(uuid.uuid4())

        # Hash the password
        hashed_password = bcrypt.hashpw(details.password.encode('utf-8'), bcrypt.gensalt())

        # Prepare buyer data (exclude plain password)
        buyer_data = details.dict()
        buyer_data['password_hash'] = hashed_password.decode('utf-8')
        del buyer_data['password']  # Remove plain password

        # Store buyer details in 'buyers' collection
        buyer_ref = db.collection("buyers").document(user_id)
        buyer_ref.set(buyer_data)
        print(f"Buyer {user_id} created in Firestore.")

        return {
            "message": "Buyer registered successfully.",
            "user_id": user_id,
            "role": "buyer"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Buyer registration failed: {str(e)}")

async def get_all_buyers():
    """
    Retrieves all registered buyers from Firestore.
    Returns a list of buyers with their user_id and all details.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        buyers_ref = db.collection("buyers")
        docs = buyers_ref.stream()

        buyers = []
        for doc in docs:
            buyer_data = doc.to_dict()
            buyer_data["user_id"] = doc.id  # Include the document ID as user_id
            buyers.append(buyer_data)

        return {
            "total_buyers": len(buyers),
            "buyers": buyers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve buyers: {str(e)}")

async def get_buyer_by_id(user_id: str):
    """
    Retrieves a specific buyer by their user_id from Firestore.
    Returns the buyer's details if found.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        buyer_ref = db.collection("buyers").document(user_id)
        doc = buyer_ref.get()

        if not doc.exists:
            raise HTTPException(status_code=404, detail="Buyer not found.")

        buyer_data = doc.to_dict()
        buyer_data["user_id"] = doc.id  # Include the document ID as user_id

        return buyer_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve buyer: {str(e)}")

async def get_user_with_products(user_id: str):
    """
    Retrieves a user's details along with all their products.
    Works for both artisans and buyers.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        # First, try to get user from artisans collection
        user_data = None
        user_role = None

        artisan_ref = db.collection("artisans").document(user_id)
        artisan_doc = artisan_ref.get()

        if artisan_doc.exists:
            user_data = artisan_doc.to_dict()
            user_data["user_id"] = artisan_doc.id
            user_role = "artisan"
        else:
            # If not found in artisans, try buyers collection
            buyer_ref = db.collection("buyers").document(user_id)
            buyer_doc = buyer_ref.get()

            if buyer_doc.exists:
                user_data = buyer_doc.to_dict()
                user_data["user_id"] = buyer_doc.id
                user_role = "buyer"
            else:
                raise HTTPException(status_code=404, detail="User not found.")

        # Get products if user is an artisan
        products = []
        if user_role == "artisan":
            products_ref = db.collection("product_stories").document(user_id).collection("products")
            products_docs = products_ref.stream()

            for product_doc in products_docs:
                product_data = product_doc.to_dict()
                product_data["product_id"] = product_doc.id
                products.append(product_data)

        return {
            "user": user_data,
            "role": user_role,
            "products": products,
            "total_products": len(products)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve user with products: {str(e)}")

# --------------------------------------------------------------
#  UNPROTECTED: Update artisan profile by user_id
# --------------------------------------------------------------
async def update_artisan_profile_unprotected(
    user_id: str,
    updates: dict
):
    """
    Unprotected: Update artisan profile by user_id.
    `updates` should be a dict with frontend keys: name, shopName, location, bio, phone, typeOfWork
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firestore not initialized.")

    artisan_ref = db.collection("artisans").document(user_id)
    doc = artisan_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Artisan not found")

    # Map frontend keys to Firestore keys
    field_map = {
        "name": "name",
        "shopName": "shop_name",
        "location": "place",
        "bio": "bio",
        "phone": "phone",
        "typeOfWork": "type_of_work"
    }

    filtered = {}
    for frontend_key, value in updates.items():
        # Accept False/0 but skip None or empty strings
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue

        firestore_key = field_map.get(frontend_key)
        if firestore_key:
            filtered[firestore_key] = value
        else:
            print(f"Warning: Ignoring unknown field '{frontend_key}'")

    if not filtered:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Optional audit metadata
    filtered["profile_last_updated_at"] = datetime.now(timezone.utc).isoformat()
    filtered["profile_last_updated_by"] = user_id

    try:
        artisan_ref.update(filtered)
        print(f"Updated artisan {user_id}: {filtered}")
        updated_doc = artisan_ref.get()
        updated_data = updated_doc.to_dict() or {}
        updated_data["user_id"] = updated_doc.id
        return {"message": "Profile updated", "updated_fields": list(filtered.keys()), "user": updated_data}
    except Exception as e:
        print(f"Firestore update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

# --------------------------------------------------------------
#  UNPROTECTED: Upload profile photo by user_id
# --------------------------------------------------------------
async def upload_profile_photo_unprotected(
    user_id: str,
    file: UploadFile = File(...)
):
    """
    Unprotected: Upload profile photo for the given user_id.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firestore is not initialized.")

    # Validate file
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG/PNG)")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5 MB
        raise HTTPException(status_code=400, detail="Image too large (max 5 MB)")

    artisan_ref = db.collection("artisans").document(user_id)
    doc = artisan_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Artisan not found.")

    artisan_data = doc.to_dict()
    old_photo_url = artisan_data.get("photo_url")

    try:
        bucket = storage.bucket()
        blob_path = f"profiles/artisans/{user_id}/photo_{int(datetime.now().timestamp())}.jpg"
        blob = bucket.blob(blob_path)

        # Delete old photo from storage if it exists
        if old_photo_url:
            try:
                old_blob_name = _get_blob_name_from_url(old_photo_url)
                if old_blob_name:
                    old_blob = bucket.blob(old_blob_name)
                    if old_blob.exists():
                        old_blob.delete()
                        print(f"Deleted old photo: {old_blob_name}")
            except Exception as e:
                print(f"Warning: Could not delete old photo: {e}")

        blob.upload_from_string(contents, content_type=file.content_type)
        # Try to make public; if bucket prevents it, return gs:// path
        try:
            blob.make_public()
            photo_url = blob.public_url
        except Exception:
            photo_url = f"gs://{bucket.name}/{blob_path}"

        artisan_ref.update({
            "photo_url": photo_url,
            "photo_updated_at": datetime.now(timezone.utc).isoformat()
        })

        print(f"Uploaded photo for {user_id}: {photo_url}")
        return {"message": "Photo uploaded", "photo_url": photo_url}
    except Exception as e:
        print(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    
# --------------------------------------------------------------
#  UNPROTECTED: Update buyer profile by user_id
# --------------------------------------------------------------
async def update_buyer_profile_unprotected(
    user_id: str,
    updates: dict
):
    """
    Unprotected: Update buyer profile by user_id.
    `updates` should be a dict with frontend keys: name, phone, deliveryAddress
    Email changes are explicitly disallowed.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firestore not initialized.")

    # Disallow email modifications
    if "email" in updates:
        raise HTTPException(status_code=400, detail="Email cannot be changed via this endpoint.")

    buyer_ref = db.collection("buyers").document(user_id)
    doc = buyer_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Buyer not found")

    # Map frontend keys to Firestore keys
    field_map = {
        "name": "name",
        "phone": "phone",
        "deliveryAddress": "delivery_address"
    }

    filtered = {}
    for frontend_key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and value.strip() == "":
            continue

        firestore_key = field_map.get(frontend_key)
        if firestore_key:
            filtered[firestore_key] = value
        else:
            print(f"Warning: Ignoring unknown field '{frontend_key}'")

    if not filtered:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    # Audit metadata
    filtered["profile_last_updated_at"] = datetime.now(timezone.utc).isoformat()
    filtered["profile_last_updated_by"] = user_id

    try:
        buyer_ref.update(filtered)
        print(f"Updated buyer {user_id}: {filtered}")
        updated_doc = buyer_ref.get()
        updated_data = updated_doc.to_dict() or {}
        updated_data["user_id"] = updated_doc.id
        return {"message": "Buyer profile updated", "updated_fields": list(filtered.keys()), "user": updated_data}
    except Exception as e:
        print(f"Firestore update failed: {e}")
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")


# --------------------------------------------------------------
#  UNPROTECTED: Upload profile photo (shared for artisans & buyers)
# --------------------------------------------------------------
async def upload_profile_photo_unprotected(
    user_id: str,
    file: UploadFile = File(...)
):
    """
    Unprotected: Upload profile photo for the given user_id.
    Works for both artisans and buyers (stores in their respective collections).
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firestore is not initialized.")

    # Validate file
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG/PNG)")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5 MB
        raise HTTPException(status_code=400, detail="Image too large (max 5 MB)")

    # Try buyer first
    buyer_ref = db.collection("buyers").document(user_id)
    doc = buyer_ref.get()
    collection = "buyers"
    if not doc.exists:
        # Fallback to artisan
        artisan_ref = db.collection("artisans").document(user_id)
        doc = artisan_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User not found.")
        buyer_ref = artisan_ref  # reuse variable
        collection = "artisans"

    try:
        bucket = storage.bucket()
        blob_path = f"profiles/{collection}/{user_id}/photo_{int(datetime.now().timestamp())}.jpg"
        blob = bucket.blob(blob_path)

        blob.upload_from_string(contents, content_type=file.content_type)
        try:
            blob.make_public()
            photo_url = blob.public_url
        except Exception:
            photo_url = f"gs://{bucket.name}/{blob_path}"

        buyer_ref.update({
            "photo_url": photo_url,
            "photo_updated_at": datetime.now(timezone.utc).isoformat()
        })

        print(f"Uploaded photo for {collection[:-1]} {user_id}: {photo_url}")
        return {"message": "Photo uploaded", "photo_url": photo_url}
    except Exception as e:
        print(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")