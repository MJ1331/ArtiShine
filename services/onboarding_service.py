# services/onboarding_service.py

import os
import datetime
import json
import uuid
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import Dict
from fastapi import HTTPException
from pydantic import BaseModel
import requests  # <-- Added for direct API calls

# Firebase Admin SDK Imports
import firebase_admin
from firebase_admin import credentials, firestore, storage

# --- Pydantic models required by the service method ---
class ArtisanID(BaseModel):
    UserID: str

class OnboardingOutput(BaseModel):
    UserID: str
    CaptionData: Dict
    ImageURL: str

# --- Global objects that will be initialized once ---
db = None
bucket = None

# --- Helper Functions (No longer LangChain tools) ---

def get_welcome_caption(name: str, shop_name: str, location: str) -> Dict:
    """Generates a social media caption by calling the OpenRouter API directly."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost", # Replace with your actual site
        "X-Title": "Artisan Onboarding API"  # Replace with your actual app name
    }
    payload = {
        "model": "deepseek/deepseek-chat-v3.1:free",
        "messages": [
            {"role": "system", "content": "You are an expert content creator for ArtiShine. Return a clean JSON object with 'caption' and 'hashtags' keys."},
            {"role": "user", "content": f"Create a warm welcome caption for our platform. Introduce the artisan, {name}, and their shop, {shop_name}, located in {location}. It's important to feature the artisan's name prominently in the welcome message."}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
    }
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        content_str = response.json()['choices'][0]['message']['content']
        return json.loads(content_str)
    except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError) as e:
        return {"error": f"Failed to generate caption via API: {e}"}


def generate_and_upload_onboarding_image(user_id: str, name: str, dob_str: str, shop_name: str, location: str) -> str:
    """Generates an onboarding image and uploads it to Firebase Storage."""
    global bucket
    if not bucket:
        raise ValueError("Firebase Storage bucket is not properly initialized.")

    try:
        image_path = r"./ARTISHIINE.png"
        font_path = r"./Pixel Game.otf"
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
        rainbow_colors=[(148,0,211),(75,0,130),(0,0,255),(0,255,0),(255,255,0),(255,127,0),(255,0,0)]
        
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
        return blob.public_url

    except Exception as e:
        raise Exception(f"Image generation or upload failed: {e}")

# --- Initialization Block ---
def initialize():
    """Initializes Firebase services."""
    global db, bucket
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred, {
                'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
            })
        db = firestore.client()
        bucket = storage.bucket()
        print("✅ Firebase initialized successfully in service.")
    except Exception as e:
        print(f"🔥 Firebase initialization failed in service: {e}")
        db = None
        bucket = None

initialize()

# --- Service Class ---
class OnboardingService:
    async def create_onboarding_post(self, details: ArtisanID) -> OnboardingOutput:
        if not db or not bucket:
            raise HTTPException(status_code=500, detail="Firebase is not initialized.")
        
        # 1. Fetch and validate artisan data from Firestore
        try:
            artisan_ref = db.collection("artisans").document(details.UserID)
            artisan_doc = artisan_ref.get()

            if not artisan_doc.exists:
                raise HTTPException(status_code=404, detail=f"Artisan with UserID '{details.UserID}' not found.")
            
            artisan_data = artisan_doc.to_dict()
            
            required_fields = ['name', 'shop_name', 'location', 'date_of_birth']
            if not all(field in artisan_data for field in required_fields):
                raise HTTPException(status_code=400, detail="Artisan document is missing required fields.")

            name, shop_name, location = artisan_data['name'], artisan_data['shop_name'], artisan_data['location']
            dob_obj = datetime.datetime.strptime(artisan_data['date_of_birth'], '%d-%m-%Y')
            dob_string = dob_obj.strftime('%Y-%m-%d')
        except HTTPException as http_exc:
            raise http_exc # Re-raise FastAPI exceptions
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch or process artisan data: {str(e)}")

        # 2. Sequentially generate content and handle errors
        try:
            # Generate caption
            caption_data = get_welcome_caption(name=name, shop_name=shop_name, location=location)
            if 'error' in caption_data:
                raise Exception(f"Caption generation failed: {caption_data['error']}")
            
            # Generate and upload image
            image_url = generate_and_upload_onboarding_image(
                user_id=details.UserID, name=name, dob_str=dob_string, 
                shop_name=shop_name, location=location
            )
            
            # 3. Save all results to Firestore
            db.collection('Onboarding_Posts').document(details.UserID).set({
                'UserID': details.UserID,
                'onboardingCaption': caption_data,
                'onboardingImageUrl': image_url
            }, merge=True)

            # 4. Return the final, structured output
            return OnboardingOutput(
                UserID=details.UserID,
                CaptionData=caption_data,
                ImageURL=image_url
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))