from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from firebase_admin import auth
from utils.firebase import get_firestore_client
import logging
from firebase_admin.firestore import SERVER_TIMESTAMP

router = APIRouter()
logger = logging.getLogger(__name__)

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str

@router.post("/register")
async def register_user(request: RegisterRequest):
    db = get_firestore_client()  # Get client inside function
    try:
        # Validate input
        if request.role not in ["artisan", "buyer"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'artisan' or 'buyer'")
        if len(request.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

        # Create user in Firebase Auth
        user = auth.create_user(
            email=request.email,
            password=request.password
        )

        # Store user data in Firestore
        db.collection('users').document(user.uid).set({
            'name': request.name,
            'email': request.email,
            'role': request.role,
            'createdAt': SERVER_TIMESTAMP
        })

        return {
            "message": "User registered successfully",
            "userId": user.uid
        }
    except auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=400, detail="Email already in use")
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")