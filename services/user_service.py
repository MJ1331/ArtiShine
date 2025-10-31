# services/user_service.py
import uuid
import bcrypt
import jwt
import datetime
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .firebase_config import db
from . import onboarding_service
from models.user_models import ArtisanDetails, BuyerDetails, LoginRequest, UserRole
from dotenv import load_dotenv
import os

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
        query = users_ref.where("email", "==", login_data.email).limit(1)
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
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)  # Token expires in 24 hours
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