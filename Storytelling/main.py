from dotenv import load_dotenv
load_dotenv()  # load environment variables

import requests
import base64
import logging
import os
import datetime
import json
import re
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# Google Cloud Storage
from google.cloud import storage

# ----------------------------
# Logger
# ----------------------------
logger = logging.getLogger("storytelling_app")
logging.basicConfig(level=logging.INFO)

# ----------------------------
# Environment Variables
# ----------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not set")
if not GOOGLE_APPLICATION_CREDENTIALS:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")
if not BUCKET_NAME:
    raise ValueError("BUCKET_NAME not set")

# ----------------------------
# Firebase & GCS Initialization
# ----------------------------
if not firebase_admin._apps:
    cred = credentials.Certificate(GOOGLE_APPLICATION_CREDENTIALS)
    firebase_admin.initialize_app(cred)

storage_client = storage.Client()

# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI()
origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Helper: Parse OpenRouter JSON
# ----------------------------
def parse_openrouter_output(raw_text: str):
    """
    Extract JSON object from OpenRouter output even if wrapped in markdown or extra text.
    """
    # Remove markdown fences
    raw_text = re.sub(r"```(json)?", "", raw_text, flags=re.IGNORECASE).strip()
    
    # Attempt to extract {...} JSON object
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted JSON. Returning raw text.")
    return {"raw_output": raw_text}

# ----------------------------
# OpenRouter Storytelling Function
# ----------------------------
def call_openrouter_storytelling(image_b64, voice_transcript, artisan_name, location):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
Classify the image into: Pottery, Painting, Food, Fabric and Clothing, Glass Artefact, Sculptures.
Generate a structured product bio using:
- Artisan's Description: {voice_transcript}
- Artisan's Name: {artisan_name}
- Location: {location}

Output as JSON with keys:
Title, Category, Tagline, ForWhom, Material, Method, CulturalSignificance, WhoMadeIt
"""

    messages_content = [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
    ]

    body = {
        "model": "mistralai/mistral-small-3.2-24b-instruct:free",
        "messages": [{"role": "user", "content": messages_content}]
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=body,
            timeout=60
        )
    except requests.RequestException as e:
        logger.error(f"Request to OpenRouter failed: {e}")
        raise HTTPException(status_code=500, detail=f"OpenRouter request failed: {e}")

    if response.status_code != 200:
        logger.error(f"OpenRouter API Error {response.status_code}: {response.text}")
        raise HTTPException(status_code=response.status_code, detail=f"OpenRouter API Error: {response.text}")

    raw_text = response.json()['choices'][0]['message']['content']
    return parse_openrouter_output(raw_text)

# ----------------------------
# API Endpoint
# ----------------------------
@app.post("/generate-story/")
async def generate_story_endpoint(
    artisan_name: str = Form(...),
    location: str = Form(...),
    voice_transcript: str = Form(...),
    image: UploadFile = File(...)
):
    if not image:
        raise HTTPException(status_code=400, detail="Image file required")

    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    logger.info(f"Received image: {len(image_bytes)} bytes, filename={image.filename}")
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Call OpenRouter storytelling
    story_content = call_openrouter_storytelling(image_b64, voice_transcript, artisan_name, location)

    story_json = {
        "artisan_name": artisan_name,
        "location": location,
        "voice_transcript": voice_transcript,
        "story": story_content,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    # Save to Firestore
    artisan_ref = firestore.client().collection("artisans").document(artisan_name)
    artisan_ref.set({"products": firestore.ArrayUnion([story_json])}, merge=True)
    firestore.client().collection("product_stories").add(story_json)

    # Save to GCS
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{artisan_name}_{timestamp}.json"
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(f"stories/{filename}")
    blob.upload_from_string(json.dumps(story_json), content_type="application/json")
    story_url = blob.public_url

    logger.info(f"Story saved successfully for {artisan_name}")
    return JSONResponse(content={"story_json": story_json, "story_file_url": story_url})
