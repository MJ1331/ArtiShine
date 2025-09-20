# main.py
import os
from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import Firebase and initialize it here, once, at startup.
import firebase_admin
from firebase_admin import credentials
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not firebase_admin._apps:
    cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
    firebase_admin.initialize_app(cred)

# Import your new router
from routes.story_router import router as story_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("storytelling_app")

app = FastAPI(title="Artisan Storytelling API")

# Add Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Or specify your frontend URL for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include your routes
app.include_router(story_router)

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Artisan Storytelling API"}