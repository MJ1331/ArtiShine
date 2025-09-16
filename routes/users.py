from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import Annotated
from firebase_admin import auth, firestore, storage
from utils.dependencies import get_current_artisan
from transcribe_audio import transcribe_audio
from fastapi.concurrency import run_in_threadpool
import logging
import os
import shutil
from tempfile import NamedTemporaryFile
from datetime import timedelta
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)
db = firestore.client()
bucket = storage.bucket()

@router.get("/me")
async def get_current_user(current_artisan: tuple = Depends(get_current_artisan)):
    user_data, uid = current_artisan
    return {
        "userId": uid,
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "role": user_data.get("role"),
        "shopName": user_data.get("shopName"),
        "address": user_data.get("address"),
        "bio": user_data.get("bio"),
        "isInstagramConnected": user_data.get("isInstagramConnected", False)
    }

@router.put("/me")
async def update_user_profile(
    name: Annotated[str, Form()] = None,
    shopName: Annotated[str, Form()] = None,
    address: Annotated[str, Form()] = None,
    current_artisan: tuple = Depends(get_current_artisan)
):
    user_data, uid = current_artisan
    update_data = {}
    updated_fields = []
    
    if name:
        update_data["name"] = name
        updated_fields.append("name")
    if shopName:
        update_data["shopName"] = shopName
        updated_fields.append("shopName")
    if address:
        update_data["address"] = address
        updated_fields.append("address")
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    
    try:
        db.collection('users').document(uid).update(update_data)
        return {
            "message": "Profile updated successfully",
            "updatedFields": updated_fields
        }
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/{artisanId}")
async def get_artisan_profile(artisanId: str):
    try:
        user_doc = db.collection('users').document(artisanId).get()
        if not user_doc.exists:
            raise HTTPException(status_code=404, detail="Artisan not found")
        user_data = user_doc.to_dict()
        if user_data.get('role') != 'artisan':
            raise HTTPException(status_code=403, detail="User is not an artisan")
        return {
            "userId": artisanId,
            "name": user_data.get("name"),
            "shopName": user_data.get("shopName"),
            "address": user_data.get("address"),
            "bio": user_data.get("bio")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get artisan profile error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/me/generate-bio")
async def generate_user_bio(
    lang: Annotated[str, Form()],
    audio: UploadFile = File(...),
    current_artisan: tuple = Depends(get_current_artisan)
):
    user_data, uid = current_artisan
    
    # Validate file
    if not audio.content_type or not audio.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files allowed.")
    if audio.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 100MB).")
    
    # Validate language code
    supported_langs = ["ta-IN", "hi-IN", "en-IN"]
    if lang not in supported_langs:
        raise HTTPException(status_code=400, detail=f"Unsupported language code. Supported: {supported_langs}")

    temp_file = None
    try:
        _, file_ext = os.path.splitext(audio.filename)
        with NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            shutil.copyfileobj(audio.file, temp_file)
            temp_file_path = temp_file.name
        
        # Upload audio to Firebase Storage
        storage_path = f"product-audio/{uid}/bio_{uuid.uuid4()}{file_ext}"
        blob = bucket.blob(storage_path)
        blob.upload_from_filename(temp_file_path)
        audio_url = blob.generate_signed_url(expiration=timedelta(days=7))
        
        # Run transcription (native) and translation (English)
        native_text = await run_in_threadpool(
            transcribe_audio, temp_file_path, lang, task="transcribe"
        )
        english_text = await run_in_threadpool(
            transcribe_audio, temp_file_path, lang, task="translate"
        )
        
        if native_text is None or english_text is None:
            raise HTTPException(status_code=500, detail="Audio processing failed")
        
        # Update artisan's bio in Firestore
        artisan_ref = db.collection('users').document(uid)
        artisan_ref.update({
            'bio': english_text,
            'native_bio': native_text,
            'bio_audio_url': audio_url,
            'bio_lang': lang,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        return {
            "message": "Bio generated and updated successfully!",
            "newBio": english_text,
            "nativeBio": native_text,
            "audioFile": audio_url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bio generation error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)