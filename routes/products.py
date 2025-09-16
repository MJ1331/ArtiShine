from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from typing import Annotated
from firebase_admin import firestore, storage
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

@router.get("/my-products")
async def get_my_products(current_artisan: tuple = Depends(get_current_artisan)):
    _, uid = current_artisan
    try:
        products = db.collection('products').where('artisanId', '==', uid).get()
        product_list = [doc.to_dict() for doc in products]
        return {"products": product_list}
    except Exception as e:
        logger.error(f"Get products error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.get("/{productId}")
async def get_product(productId: str):
    try:
        product_doc = db.collection('products').document(productId).get()
        if not product_doc.exists:
            raise HTTPException(status_code=404, detail="Product not found")
        product_data = product_doc.to_dict()
        artisan_doc = db.collection('users').document(product_data['artisanId']).get()
        if not artisan_doc.exists:
            raise HTTPException(status_code=404, detail="Artisan not found")
        artisan_data = artisan_doc.to_dict()
        return {
            "productId": productId,
            "title": product_data.get("title"),
            "tagline": product_data.get("tagline"),
            "story": product_data.get("story"),
            "imageUrl": product_data.get("imageUrl"),
            "artisan": {
                "userId": product_data['artisanId'],
                "name": artisan_data.get("name"),
                "shopName": artisan_data.get("shopName")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.put("/{productId}")
async def update_product(
    productId: str,
    title: Annotated[str, Form()] = None,
    tagline: Annotated[str, Form()] = None,
    story: Annotated[str, Form()] = None,
    current_artisan: tuple = Depends(get_current_artisan)
):
    _, uid = current_artisan
    try:
        product_doc = db.collection('products').document(productId).get()
        if not product_doc.exists:
            raise HTTPException(status_code=404, detail="Product not found")
        if product_doc.to_dict()['artisanId'] != uid:
            raise HTTPException(status_code=403, detail="Not authorized to update this product")
        
        update_data = {}
        updated_fields = []
        if title:
            update_data["title"] = title
            updated_fields.append("title")
        if tagline:
            update_data["tagline"] = tagline
            updated_fields.append("tagline")
        if story:
            update_data["story"] = story
            updated_fields.append("story")
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        
        db.collection('products').document(productId).update(update_data)
        return {"message": "Product updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update product error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.delete("/{productId}")
async def delete_product(productId: str, current_artisan: tuple = Depends(get_current_artisan)):
    _, uid = current_artisan
    try:
        product_doc = db.collection('products').document(productId).get()
        if not product_doc.exists:
            raise HTTPException(status_code=404, detail="Product not found")
        product_data = product_doc.to_dict()
        if product_data['artisanId'] != uid:
            raise HTTPException(status_code=403, detail="Not authorized to delete this product")
        
        # Delete associated files from storage
        if product_data.get('imageUrl'):
            image_blob = bucket.blob(product_data['imageUrl'].split(f"{bucket.name}/")[1])
            image_blob.delete()
        if product_data.get('audioUrl'):
            audio_blob = bucket.blob(product_data['audioUrl'].split(f"{bucket.name}/")[1])
            audio_blob.delete()
        
        # Delete product document
        db.collection('products').document(productId).delete()
        return {"message": "Product deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete product error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/generate")
async def generate_product_description(
    lang: Annotated[str, Form()],
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    post_to_instagram: Annotated[bool, Form()] = False,
    current_artisan: tuple = Depends(get_current_artisan)
):
    user_data, uid = current_artisan
    
    # Validate files
    if not audio or not image:
        raise HTTPException(status_code=400, detail="Both audio and image files are required")
    if not audio.content_type or not audio.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Invalid image file type")
    if audio.size > 100 * 1024 * 1024 or image.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 100MB)")
    
    # Validate language code
    supported_langs = ["ta-IN", "hi-IN", "en-IN"]
    if lang not in supported_langs:
        raise HTTPException(status_code=400, detail=f"Unsupported language code. Supported: {supported_langs}")

    temp_audio_file = None
    temp_image_file = None
    try:
        _, audio_ext = os.path.splitext(audio.filename)
        _, image_ext = os.path.splitext(image.filename)
        
        with NamedTemporaryFile(delete=False, suffix=audio_ext) as temp_audio_file, \
             NamedTemporaryFile(delete=False, suffix=image_ext) as temp_image_file:
            shutil.copyfileobj(audio.file, temp_audio_file)
            shutil.copyfileobj(image.file, temp_image_file)
            temp_audio_path = temp_audio_file.name
            temp_image_path = temp_image_file.name
        
        # Upload files to Firebase Storage
        audio_storage_path = f"product-audio/{uid}/{uuid.uuid4()}{audio_ext}"
        image_storage_path = f"product-images/{uid}/{uuid.uuid4()}{image_ext}"
        
        audio_blob = bucket.blob(audio_storage_path)
        image_blob = bucket.blob(image_storage_path)
        audio_blob.upload_from_filename(temp_audio_path)
        image_blob.upload_from_filename(temp_image_path)
        
        audio_url = audio_blob.generate_signed_url(expiration=timedelta(days=7))
        image_url = image_blob.generate_signed_url(expiration=timedelta(days=7))
        
        # Run transcription (native) and translation (English)
        native_text = await run_in_threadpool(
            transcribe_audio, temp_audio_path, lang, task="transcribe"
        )
        english_text = await run_in_threadpool(
            transcribe_audio, temp_audio_path, lang, task="translate"
        )
        
        if native_text is None or english_text is None:
            raise HTTPException(status_code=500, detail="Audio processing failed")
        
        # Placeholder for Vision AI and Gemini integration
        generated_content = {
            "title": native_text[:50],
            "tagline": english_text[:100],
            "story": english_text,
            "native_title": native_text[:50],
            "native_tagline": native_text[:100],
            "native_story": native_text,
            "category": "Craft"
        }
        
        # Save to Firestore products collection
        product_id = f"prod_{uuid.uuid4().hex}"
        product_entry = {
            "productId": product_id,
            "artisanId": uid,
            "title": generated_content["title"],
            "tagline": generated_content["tagline"],
            "story": generated_content["story"],
            "native_title": generated_content["native_title"],
            "native_tagline": generated_content["native_tagline"],
            "native_story": generated_content["native_story"],
            "category": generated_content["category"],
            "imageUrl": image_url,
            "audioUrl": audio_url,
            "lang": lang,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        db.collection('products').document(product_id).set(product_entry)
        
        # Placeholder for Instagram posting
        if post_to_instagram:
            logger.info("Instagram posting not implemented yet")
        
        return {
            "message": "Product created successfully with AI!",
            "productId": product_id,
            "generatedContent": generated_content
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generate product error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if temp_audio_file and os.path.exists(temp_audio_file.name):
            os.unlink(temp_audio_file.name)
        if temp_image_file and os.path.exists(temp_image_file.name):
            os.unlink(temp_image_file.name)