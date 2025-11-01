import uuid
from typing import List, Dict, Optional
from fastapi import UploadFile, HTTPException
import datetime
import re

# Import our centralized configs and services
from .firebase_config import db, bucket
from . import ai_services, instagram_service
from firebase_admin import firestore
from urllib.parse import unquote

# --------------------------
# Helper: parse blob name from a public URL or gs:// URL
# --------------------------
def _get_blob_name_from_url(url: str) -> Optional[str]:
    """
    Extracts the correct blob name from a GCS public URL.
    Handles URL encoding (e.g., %20, %2520 → space).
    """
    if not url or not bucket:
        return None

    bucket_name = bucket.name
    public_prefix = f"https://storage.googleapis.com/{bucket_name}/"
    if url.startswith(public_prefix):
        encoded_path = url[len(public_prefix):]
        return unquote(encoded_path)

    # Fallback for gs:// URLs
    gs_prefix = f"gs://{bucket_name}/"
    if url.startswith(gs_prefix):
        encoded_path = url[len(gs_prefix):]
        return unquote(encoded_path)

    # Last-ditch fallback
    try:
        parts = url.split(f"/{bucket_name}/", 1)
        if len(parts) > 1:
            return unquote(parts[1])
    except:
        pass

    return None

# --------------------------
# 1. create_new_product (kept from your existing code)
# --------------------------
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
        language_code = artisan_data.get("language", "en-US")  # e.g., "hi-IN"
        print(f"Using language code: {language_code}")

        # --- 1. Upload Files to GCS ---
        image_urls = []
        image_bytes_list = []

        for image in images:
            file_bytes = await image.read()
            await image.seek(0)

            file_name = f"{user_id}/products/{product_id}/{uuid.uuid4()}_{image.filename}"
            blob = bucket.blob(file_name)
            # Upload from the UploadFile file-like object
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
            transcript = ""  # Ensure transcript is an empty string
        else:
            print(f"Transcript: {transcript}")

        # --- 3. Translate Text ---
        translated_text = ai_services.translate_text_gcp(transcript, target_language="en")

        # --- MODIFICATION: Removed the hard failure ---
        if not translated_text:
            # Don't fail the request. Log it and continue.
            print("🔥 Translation failed or returned empty. Proceeding without transcript.")
            translated_text = ""  # Ensure translated_text is an empty string
        else:
            print(f"Translated Text: {translated_text}")

        # Save transcript to Firestore (it will save empty strings if failed)
        db.collection("product_stories").document(user_id).collection("products").document(product_id).set({
            "voice_transcript_original": transcript,
            "voice_transcript_english": translated_text
        }, merge=True)

        # --- 4. Generate Product Story (Vertex AI) ---
        if translated_text:
            print("Transcript found. Generating story with audio description.")
            artisan_description_prompt = f"Artisan's Spoken Description: \"{translated_text}\""
        else:
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
                "location": artisan_data.get('place'),
                "latitude": artisan_data.get('latitude'),
                "longitude": artisan_data.get('longitude')
            },
            "story": story_data,
            "image_urls": image_urls,
            "timestamp": firestore.SERVER_TIMESTAMP
        }
        db.collection("product_stories").document(user_id).collection("products").document(product_id).set(final_data_for_db, merge=True)

        # --- 6. Auto-Post to Instagram ---
        # await instagram_service.post_product(user_id, product_id)

        # --- 7. FIX: Create a JSON-serializable response ---
        response_data = final_data_for_db.copy()
        response_data["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return response_data

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Product creation workflow failed: {str(e)}")

# --------------------------
# 2. get_all_products (kept)
# --------------------------
async def get_all_products():
    """
    Retrieves all products from all artisans in Firestore.
    Returns a list of all products with their details and associated user_id.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        all_products = []

        # Get all artisans to know which user_ids to check for products
        artisans_ref = db.collection("artisans")
        artisans_docs = artisans_ref.stream()

        for artisan_doc in artisans_docs:
            user_id = artisan_doc.id
            artisan_data = artisan_doc.to_dict()

            # Check if this user has any products
            products_ref = db.collection("product_stories").document(user_id).collection("products")
            products_docs = products_ref.stream()

            for product_doc in products_docs:
                product_data = product_doc.to_dict()
                product_data["user_id"] = user_id
                product_data["product_id"] = product_doc.id

                # Ensure artisan_details includes latitude and longitude
                if "artisan_details" in product_data:
                    product_data["artisan_details"]["latitude"] = artisan_data.get('latitude')
                    product_data["artisan_details"]["longitude"] = artisan_data.get('longitude')

                all_products.append(product_data)

        return {
            "total_products": len(all_products),
            "products": all_products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve products: {str(e)}")

# --------------------------
# 3. get_products_by_user_id (kept)
# --------------------------
async def get_products_by_user_id(user_id: str):
    """
    Retrieves all products for a specific user_id from Firestore.
    Returns a list of products with their details.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        products_ref = db.collection("product_stories").document(user_id).collection("products")
        products_docs = products_ref.stream()

        products = []
        for product_doc in products_docs:
            product_data = product_doc.to_dict()
            product_data["user_id"] = user_id
            product_data["product_id"] = product_doc.id
            products.append(product_data)

        return {
            "user_id": user_id,
            "total_products": len(products),
            "products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve products for user {user_id}: {str(e)}")

# --------------------------
# 4. get_all_artisans_with_images (kept)
# --------------------------
async def get_all_artisans_with_images():
    """
    Retrieves all artisans with their details (place, latitude, longitude) and all their product images.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        artisans_with_images = []
        # Get all artisans
        artisans_ref = db.collection("artisans")
        artisans_docs = artisans_ref.stream()
        for artisan_doc in artisans_docs:
            user_id = artisan_doc.id
            artisan_data = artisan_doc.to_dict()

            # Get all product images for this artisan
            product_images = []
            products_ref = db.collection("product_stories").document(user_id).collection("products")
            products_docs = products_ref.stream()

            for product_doc in products_docs:
                product_data = product_doc.to_dict()
                if "image_urls" in product_data:
                    product_images.extend(product_data["image_urls"])

            # Get onboarding post data
            onboarding_post = None
            if db:
                try:
                    onboarding_doc = db.collection('Onboarding_Posts').document(user_id).get()
                    if onboarding_doc.exists:
                        onboarding_post = onboarding_doc.to_dict()
                except Exception as e:
                    print(f"Error getting onboarding post for {user_id}: {str(e)}")

            # Create artisan object with details and images
            artisan_info = {
                "user_id": user_id,
                "name": artisan_data.get('name'),
                "email": artisan_data.get('email'),
                "phone_number": artisan_data.get('phone_number'),
                "shop_name": artisan_data.get('shop_name'),
                "place": artisan_data.get('place'),
                "latitude": artisan_data.get('latitude'),
                "longitude": artisan_data.get('longitude'),
                "product_images": product_images,
                "onboarding_post": onboarding_post
            }

            artisans_with_images.append(artisan_info)

        return {
            "total_artisans": len(artisans_with_images),
            "artisans": artisans_with_images
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve artisans with images: {str(e)}")

# --------------------------
# 5. delete_product (NEW)
# --------------------------
async def delete_product(user_id: str, product_id: str):
    """
    Deletes a product document and attempts to delete its images from the storage bucket.
    - user_id: owner of product
    - product_id: id of the product doc under product_stories/{user_id}/products/{product_id}
    Returns a simple JSON message on success.
    """
    if not db or not bucket:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    try:
        product_ref = db.collection("product_stories").document(user_id).collection("products").document(product_id)
        product_doc = product_ref.get()
        if not product_doc.exists:
            raise HTTPException(status_code=404, detail="Product not found.")

        product_data = product_doc.to_dict()

        # Attempt to delete images (best-effort)
        image_urls = product_data.get("image_urls", []) or []
        deletion_errors = []
        for url in image_urls:
            blob_name = _get_blob_name_from_url(url)
            if blob_name:
                try:
                    blob = bucket.blob(blob_name)
                    blob.delete()
                    print(f"Deleted blob {blob_name}")
                except Exception as e:
                    deletion_errors.append(f"Failed to delete blob {blob_name}: {str(e)}")
                    print(f"Failed to delete blob {blob_name}: {str(e)}")
            else:
                print(f"Could not parse blob name for URL: {url}")

        # Delete the Firestore document
        product_ref.delete()
        print(f"Deleted Firestore product {product_id} for user {user_id}")

        result = {"detail": "Product deleted."}
        if deletion_errors:
            # Return success but list errors (not raising because product doc is deleted successfully)
            result["storage_deletion_errors"] = deletion_errors

        return result

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

# --------------------------
# 6. update_product_partially (NEW)
# --------------------------
async def update_product_partially(user_id: str, product_id: str, patch_data: Dict):
    """
    Partial update (PATCH) of a product's story subfields.
    Allowed updates (case-insensitive keys):
      - title / Title
      - tagline / Tagline
      - category / Category
      - material / Material
      - method / Method
      - forwhom / ForWhom

    Disallowed fields (will raise 400):
      - CulturalSignificance (cannot be edited)
      - image_urls (images cannot be changed via this route)
      - voice_transcript_* (shouldn't be changed here)
      - product_id / user_id (identifiers cannot be changed)

    Returns the updated product document data.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")

    if not isinstance(patch_data, dict) or not patch_data:
        raise HTTPException(status_code=400, detail="Invalid or empty patch data.")

    # Normalize keys to lowercase for checking and mapping
    normalized_keys = {k.lower(): k for k in patch_data.keys()}

    # Disallowed check
    disallowed_lower = {
        "culturalsignificance", "image_urls", "imageurls", "voice_transcript_original",
        "voice_transcript_english", "product_id", "user_id"
    }
    for lower_k in normalized_keys:
        if lower_k in disallowed_lower:
            raise HTTPException(status_code=400, detail=f"Field '{normalized_keys[lower_k]}' is not allowed to be updated.")

    # Mapping from lowercase input key -> story key name
    allowed_map = {
        "title": "Title",
        "tagline": "Tagline",
        "category": "Category",
        "material": "Material",
        "method": "Method",
        "forwhom": "ForWhom",
        "for_whom": "ForWhom"
    }

    # Build story updates
    story_updates = {}
    for lower_k, original_k in normalized_keys.items():
        if lower_k in allowed_map:
            target_field = allowed_map[lower_k]
            story_updates[target_field] = patch_data[original_k]
        else:
            # Unknown fields are ignored; alternatively we could raise an error
            # For safety we will ignore unknown fields quietly
            print(f"Ignoring unknown/unsupported field in patch: {original_k}")

    if not story_updates:
        raise HTTPException(status_code=400, detail="No valid updatable fields found in patch data.")

    try:
        product_ref = db.collection("product_stories").document(user_id).collection("products").document(product_id)
        product_doc = product_ref.get()
        if not product_doc.exists:
            raise HTTPException(status_code=404, detail="Product not found.")

        # Merge story updates into existing story subdocument
        # Use set(..., merge=True) to update only passed fields
        update_payload = {
            "story": story_updates,
            "updated_at": firestore.SERVER_TIMESTAMP
        }
        product_ref.set(update_payload, merge=True)

        # Return the updated document snapshot
        updated_doc = product_ref.get()
        updated_data = updated_doc.to_dict()
        updated_data["product_id"] = product_id
        updated_data["user_id"] = user_id

        # Convert Firestore SERVER_TIMESTAMP to ISO if present? (keep as-is, client can display)
        return updated_data

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")
