import os
from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils.firebase import init_firebase, get_db
from datetime import datetime

# Firebase Admin SDK initialization
import firebase_admin
from firebase_admin import credentials

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Artisan AI and Storytelling API")

# Initialize Firebase
init_firebase()

# Import routers after Firebase initialization
from routes.auth import router as auth_router
from routes.users import router as users_router
from routes.products import router as products_router
from routes.ai_generate import router as ai_generate_router
from routes.discover import router as discover_router
from routes.story_router import router as story_router

# Load model and test Firebase connection at startup
@app.on_event("startup")
async def startup_event():
    try:
        # Test Firebase connections
        db = get_db()
        db.collection('test').document('ping').set({'status': 'ok'})
        logger.info("Firestore connection test successful")
    except Exception as e:
        logger.error(f"Startup error (Model or Firebase): {e}")
        raise

# CORS Middleware for frontend communication
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "*"  # From file 2, allowing all origins (less secure, can be restricted later)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth")
app.include_router(users_router, prefix="/users")
app.include_router(products_router, prefix="/products")
app.include_router(ai_generate_router, prefix="/ai")
app.include_router(discover_router, prefix="/discover")
app.include_router(story_router, prefix="/stories")

# Root endpoint (combined from both files)
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Artisan AI and Storytelling API"}

# Dummy Registration Endpoint (from file 1)
@app.get("/register")
async def register_user(
    username: str,
    password: str,
    location: str,
    email: str | None = None,
    role: str | None = None,
    shopName: str | None = None
):
    db = get_db()
    try:
        # Validate input
        if not username or not password or not location:
            raise HTTPException(status_code=400, detail="Username, password, and location are required")
        if role and role not in ["artisan", "buyer"]:
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'artisan' or 'buyer'")

        # Create user data object
        user_data = {
            "username": username,
            "password": password,  
            "location": location,
            "email": email,
            "role": role or "artisan",  
            "shopName": shopName,
            "createdAt": db.SERVER_TIMESTAMP,
            "createdAtReadable": datetime.now().isoformat()  # For readability in testing
        }

        # Store in Firestore under pending_users collection
        doc_ref = db.collection("pending_users").document()
        doc_ref.set(user_data)

        logger.info(f"Stored user data for {username} in pending_users collection")

        return {
            "message": "User details stored successfully in pending_users collection",
            "userId": doc_ref.id,
            "data": user_data
        }
    except Exception as e:
        logger.error(f"Dummy register error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")