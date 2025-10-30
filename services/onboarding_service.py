import os
import datetime  # <-- ADD THIS IMPORT
import json
import uuid
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from fastapi import HTTPException

# Import our centralized configs and services
from .firebase_config import db, bucket
from . import ai_services, instagram_service
from firebase_admin import firestore

async def generate_and_post_onboarding(user_id: str) -> dict:
    """
    Orchestrates the full onboarding post generation and posting.
    """
    if not db or not bucket:
        raise HTTPException(status_code=500, detail="Firebase is not initialized.")
    
    # 1. Fetch and validate artisan data
    try:
        artisan_ref = db.collection("artisans").document(user_id)
        artisan_doc = artisan_ref.get()
        if not artisan_doc.exists:
            raise HTTPException(status_code=404, detail="Artisan not found.")
        
        artisan_data = artisan_doc.to_dict()
        name = artisan_data['name']
        shop_name = artisan_data['shop_name']
        location = artisan_data['place'] # From your new model
        
        # Your workflow gets DOB as 'DD-MM-YYYY'
        dob_obj = datetime.datetime.strptime(artisan_data['date_of_birth'], '%d-%m-%Y')
        # The image function needs 'YYYY-MM-DD'
        dob_string_for_image = dob_obj.strftime('%Y-%m-%d')

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process artisan data: {str(e)}")

    # 2. Generate content using Google Cloud
    try:
        # --- Generate Caption (using Vertex AI) ---
        prompt = f"""
        You are an expert content creator for ArtiShine. 
        Create a warm welcome caption for our platform. 
        Introduce the artisan, {name}, and their shop, {shop_name}, located in {location}. 
        It's important to feature the artisan's name prominently.
        Return a clean JSON object with 'caption' and 'hashtags' keys.
        """
        caption_data = ai_services.generate_json_from_text_gcp(prompt)
        if 'error' in caption_data:
            raise Exception(f"Caption generation failed: {caption_data['error']}")
        
        # --- Generate Image (using your Pillow logic) ---
        image_url = _generate_and_upload_image(
            user_id=user_id, name=name, dob_str=dob_string_for_image, 
            shop_name=shop_name, location=location
        )
        
        # 3. Save results to Firestore
        # --- MODIFICATION: Renamed variable ---
        post_data_for_db = {
            'UserID': user_id,
            'onboardingCaption': caption_data,
            'onboardingImageUrl': image_url,
            'createdAt': firestore.SERVER_TIMESTAMP  # <-- This is the Sentinel
        }
        db.collection('Onboarding_Posts').document(user_id).set(post_data_for_db)

        # 4. --- WORKFLOW STEP 3: Auto-Post to Instagram ---
        print(f"Triggering Instagram post for onboarding {user_id}...")
        await instagram_service.post_onboarding(user_id)

        # 5. --- FIX: Create a JSON-serializable response ---
        # We can't return the 'firestore.SERVER_TIMESTAMP' object to FastAPI
        response_data = {
            'UserID': user_id,
            'onboardingCaption': caption_data,
            'onboardingImageUrl': image_url,
            # Return a normal ISO string timestamp instead
            'createdAt': datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

        return response_data  # <-- Return the clean, serializable data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _generate_and_upload_image(user_id: str, name: str, dob_str: str, shop_name: str, location: str) -> str:
    """
    Generates an onboarding image and uploads it to Firebase Storage.
    (This is your original function, with corrected asset paths)
    """
    global bucket
    if not bucket:
        raise ValueError("Firebase Storage bucket is not properly initialized.")

    try:
        # --- Corrected paths to work from services/ dir ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(base_dir, '..', 'assets', 'ARTISHIINE.png')
        font_path = os.path.join(base_dir, '..', 'assets', 'Pixel Game.otf')
        # --- End of path correction ---
        
        image = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(image)
        dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        lines = [
            ("INTRODUCING","",250,30,False),
            ("ARTISAN","",250,0,False),
            ("",name,180,20,True),
            ("Shop : ",shop_name,120,50,True),
            ("Location : ",location,120,60,True),
            ("Age : ",f"{age} years",120,0,False)
        ]
        
        W, H = image.size
        y = 250
        rainbow_colors=[(148,0,211),(75,0,130),(0,0,255),(0,255,0),(255,20,147),(255,127,0),(255,0,0)]
        
        for (label, value, size, extra_space, rainbow) in lines:
            font = ImageFont.truetype(font_path, size)
            if rainbow:
                label_width = draw.textlength(label, font=font)
                total_value_width = sum(draw.textlength(c, font=font) for c in value)
                total_width = label_width + total_value_width
                x = (W - total_width) / 2
                draw.text((x, y), label, font=font, fill=(0, 0, 0))
                x += label_width
                for i, char in enumerate(value):
                    color = rainbow_colors[i % len(rainbow_colors)]
                    draw.text((x, y), char, font=font, fill=color)
                    x += draw.textlength(char, font=font)
                text_height = font.getbbox(label + value)[3]
            else:
                full_text = label + value
                text_height = font.getbbox(full_text)[3]
                x = W / 2
                draw.text((x, y), full_text, font=font, fill=(0, 0, 0), anchor="mm")
            y += text_height + extra_space

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        buffered.seek(0)

        file_name = f"onboarding_images/{user_id}/{uuid.uuid4()}.png"
        blob = bucket.blob(file_name)
        blob.upload_from_file(buffered, content_type='image/png')
        blob.make_public()
        print(f"Onboarding image uploaded to {blob.public_url}")
        return blob.public_url

    except Exception as e:
        raise Exception(f"Image generation or upload failed: {e}")