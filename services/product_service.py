import uuid
from typing import List
from fastapi import UploadFile, HTTPException
import datetime  

# Import our centralized configs and services
from .firebase_config import db, bucket
from . import ai_services, instagram_service
from firebase_admin import firestore

async def create_new_product(user_id: str, images: List[UploadFile], voice_file: UploadFile):
    """
    Orchestrates the full new product workflow.
    """
    if not db or not bucket:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    product_id = str(uuid.uuid4())
    print(f"Starting new product workflow for User: {user_id}, Product: {product_id}")

    try:
        # --- 0. Get User Language ---
        artisan_doc = db.collection("artisans").document(user_id).get()
        if not artisan_doc.exists:
            raise HTTPException(status_code=404, detail="Artisan not found.")
        artisan_data = artisan_doc.to_dict()
        language_code = artisan_data.get("language", "en-US") # e.g., "hi-IN"
        print(f"Using language code: {language_code}")

        # --- 1. Upload Files to GCS ---
        image_urls = []
        image_bytes_list = []
        
        for image in images:
            file_bytes = await image.read()
            await image.seek(0) 
            
            file_name = f"{user_id}/products/{product_id}/{uuid.uuid4()}_{image.filename}"
            blob = bucket.blob(file_name)
            blob.upload_from_file(image.file, content_type=image.content_type)
            blob.make_public()
            
            image_urls.append(blob.public_url)
            image_bytes_list.append(file_bytes)
        print(f"Uploaded {len(image_urls)} images.")

        voice_filename = f"{user_id}/products/{product_id}/{voice_file.filename}" 
        voice_blob = bucket.blob(voice_filename)
        voice_blob.upload_from_file(voice_file.file, content_type=voice_file.content_type)
        voice_blob.make_public()
        gcs_uri = f"gs://{bucket.name}/{voice_blob.name}"
        print(f"Uploaded voice file to {gcs_uri}")

        # --- 2. Transcribe Audio (STT) ---
        transcript = ai_services.transcribe_audio_gcp(
            gcs_uri=gcs_uri, 
            language_code=language_code, 
            content_type=voice_file.content_type
        )
        
        # --- MODIFICATION: Removed the hard failure ---
        if not transcript:
            # Don't fail the request. Just log it and continue.
            print("🔥 Audio transcription failed or returned empty. Proceeding without transcript.")
            transcript = "" # Ensure transcript is an empty string
        else:
            print(f"Transcript: {transcript}")

        # --- 3. Translate Text ---
        translated_text = ai_services.translate_text_gcp(transcript, target_language="en")
        
        # --- MODIFICATION: Removed the hard failure ---
        if not translated_text:
            # Don't fail the request. Log it and continue.
            print("🔥 Translation failed or returned empty. Proceeding without transcript.")
            translated_text = "" # Ensure translated_text is an empty string
        else:
            print(f"Translated Text: {translated_text}")
            
        # Save transcript to Firestore (it will save empty strings if failed)
        db.collection("product_stories").document(user_id).collection("products").document(product_id).set({
            "voice_transcript_original": transcript,
            "voice_transcript_english": translated_text
        }, merge=True)

        # --- 4. Generate Product Story (Vertex AI) ---
        
        # --- MODIFICATION: Create a conditional prompt ---
        if translated_text:
            # If we have a transcript, use the detailed prompt
            print("Transcript found. Generating story with audio description.")
            artisan_description_prompt = f"Artisan's Spoken Description: \"{translated_text}\""
        else:
            # If audio failed, use an image-only prompt
            print("Transcript not found. Generating story from images only.")
            artisan_description_prompt = "You do not have an artisan's spoken description. Base your story *only* on the visual evidence in the images."
        
        prompt = f"""
        You are an expert cultural product storyteller. Your task is to visually analyze 
        product images and combine that with an artisan's description (if provided) to generate a 
        compelling story. 
        
        Analyze the artisan's spoken description (if present) and product images to generate a structured story.
        {artisan_description_prompt}
        
        Artisan's Details: 
        - Name: {artisan_data.get('name')}
        - Shop Name: {artisan_data.get('shop_name')}
        - Location: {artisan_data.get('place')}
        
        Classify the product into one of these categories: 
        Pottery, Painting, Food, Fabric and Clothing, Glass Artefact, Sculptures.
        
        Then, generate a JSON object with keys: "Title", "Category", "Tagline", 
        "ForWhom", "Material", "Method", "CulturalSignificance", "WhoMadeIt".
        The "WhoMadeIt" key should be an object containing the artisan's details.
        The story must be inspired by the visuals in the images.
        """
        # --- END OF MODIFICATION ---
        
        story_data = ai_services.generate_json_from_multimodal_gcp(prompt, image_bytes_list)
        if 'error' in story_data:
            # This is a hard failure, because we can't post without a story
            raise Exception(f"Story generation failed: {story_data['error']}")
        print("Product story generated.")

        # --- 5. Save Final Data to Firestore ---
        final_data_for_db = {
            "user_id": user_id,
            "product_id": product_id,
            "artisan_details": {
                "name": artisan_data.get('name'),
                "shop_name": artisan_data.get('shop_name'),
                "location": artisan_data.get('place')
            },
            "story": story_data,
            "image_urls": image_urls,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        db.collection("product_stories").document(user_id).collection("products").document(product_id).set(final_data_for_db, merge=True)

        # --- 6. Auto-Post to Instagram ---
        print(f"Triggering Instagram post for product {product_id}...")
        await instagram_service.post_product(user_id, product_id)

        # --- 7. FIX: Create a JSON-serializable response ---
        response_data = final_data_for_db.copy() 
        response_data["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return response_data

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Product creation workflow failed: {str(e)}")