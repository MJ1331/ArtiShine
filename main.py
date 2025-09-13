import shutil
import uuid
import logging
from tempfile import NamedTemporaryFile
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import Annotated, Optional, Union  # Added Union
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from transcribe_audio import load_model, transcribe_audio

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SERVICE_ACCOUNT_KEY_PATH = os.getenv("SERVICE_ACCOUNT_KEY_PATH")
if not SERVICE_ACCOUNT_KEY_PATH:
    raise ValueError("SERVICE_ACCOUNT_KEY_PATH environment variable not set.")

STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
if not STORAGE_BUCKET:
    raise ValueError("FIREBASE_STORAGE_BUCKET environment variable not set.")

# Initialize Firebase with storageBucket option
cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
firebase_admin.initialize_app(
    cred,
    options={
        'storageBucket': STORAGE_BUCKET  # e.g., 'artisan-ai-backend.appspot.com'
    }
)
db = firestore.client()
bucket = storage.bucket()

# Initialize FastAPI app
app = FastAPI()

# Load model at startup
@app.on_event("startup")
async def startup_event():
    try:
        load_model()
        # Test Firebase connections
        db.collection('test').document('ping').set({'status': 'ok'})
        logger.info("Firestore connection test successful")
        bucket.blob('test/ping.txt').upload_from_string('ok')
        logger.info("Storage connection test successful")
    except Exception as e:
        logger.error(f"Startup error (Firebase or model): {e}")
        raise

# CORS Middleware for frontend communication
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Artisan AI Backend!"}

# Transcription endpoint (public for testing, no auth required)
@app.post("/transcribe-audio/")
async def transcribe_audio_endpoint(
    artisan_name: Annotated[str, Form()],
    product_name: Annotated[str, Form()],
    lang: Annotated[Union[str, None], Form()] = None,  # Fixed: Use Union + = None, no default in Form()
    file: UploadFile = File(...)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Validate file
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files allowed.")
    if file.size > 100 * 1024 * 1024:  # 100MB limit
        raise HTTPException(status_code=400, detail="File too large (max 100MB).")
    
    temp_file = None
    try:
        
        _, file_ext = os.path.splitext(file.filename)
        with NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        # Upload audio to Firebase Storage
        storage_path = f"audios/test_uploads/{artisan_name}/{product_name}_{uuid.uuid4()}{file_ext}"
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(temp_file_path)
        audio_url = blob.public_url  # Use generate_signed_url() for private buckets
        
        # Run transcription in threadpool
        transcribed_text = await run_in_threadpool(
            transcribe_audio, temp_file_path, lang
        )
        
        if transcribed_text is None:
            raise HTTPException(status_code=500, detail="Transcription failed")
        
        # Create product JSON object
        product_entry = {
            "name": product_name,
            "bio": transcribed_text,
            "audio_file": audio_url
        }
        
        # Store in Firestore under artisans collection
        artisan_ref = db.collection('artisans').document(artisan_name)
        artisan_ref.set({
            "name": artisan_name,
            "products": firestore.ArrayUnion([product_entry])
        }, merge=True)
        
        # Store transcription entry
        db.collection('transcriptions').add({
            'artisan_name': artisan_name,
            'product_name': product_name,
            'text': transcribed_text,
            'audio_url': audio_url,
            'lang': lang or 'auto',
            'timestamp': firestore.SERVER_TIMESTAMP
        })
        
        # Return only bio and audio_file as requested
        return {
            "bio": transcribed_text,
            "audio_file": audio_url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)