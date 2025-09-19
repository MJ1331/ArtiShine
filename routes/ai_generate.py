from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from typing import Annotated, Union
from firebase_admin import firestore, storage
import logging
import os
import shutil
from tempfile import NamedTemporaryFile
from datetime import timedelta
import uuid
from services.transcribe_audio import transcribe_audio
from fastapi.concurrency import run_in_threadpool

router = APIRouter()
logger = logging.getLogger(__name__)
db = firestore.client()
bucket = storage.bucket()

@router.post("/transcribe-audio/")
async def transcribe_audio_endpoint(
    artisan_name: Annotated[str, Form()],
    product_name: Annotated[str, Form()],
    lang: Annotated[Union[str, None], Form()] = None,
    file: UploadFile = File(...)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Validate file
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only audio files allowed.")
    if file.size > 100 * 1024 * 1024:
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
        audio_url = blob.generate_signed_url(expiration=timedelta(days=7))
        
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
        
        return {
            "bio": transcribed_text,
            "audio_file": audio_url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)