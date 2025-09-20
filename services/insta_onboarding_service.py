# services/instagram_poster.py
import os
import requests
import traceback
from dotenv import load_dotenv
from instagrapi import Client
from firebase_admin import credentials, initialize_app, firestore

# --- Firebase initialization is now handled directly in the service layer ---
load_dotenv()
db = None
try:
    cred = credentials.Certificate(os.getenv('SERVICE_ACCOUNT_KEY_PATH'))
    initialize_app(cred, {
        'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
    })
    db = firestore.client()
    print("Firebase initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase: {e}")

# --- Core Business Logic ---
def get_onboarding_post(user_id: str) -> dict | None:
    """Get an onboarding post document from Firestore by UserID."""
    if not db:
        print("Firestore client is not available.")
        return None
    try:
        doc_ref = db.collection('Onboarding_Posts').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            print(f"Successfully found onboarding post for UserID: {user_id}")
            return doc.to_dict()
        else:
            print(f"No onboarding post found for UserID: {user_id}")
            return None
    except Exception as e:
        print(f"Error getting onboarding post: {str(e)}")
        return None

def post_to_instagram(post_data: dict) -> bool:
    """Post an onboarding post to Instagram."""
    image_path = None
    try:
        cl = Client()
        cl.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
        img_url = post_data.get('onboardingImageUrl')
        if not img_url: return False
        
        temp_dir = os.path.abspath('temp')
        os.makedirs(temp_dir, exist_ok=True)
        response = requests.get(img_url)

        if response.status_code == 200:
            user_id = post_data.get('UserID', 'temp_post')
            image_path = os.path.join(temp_dir, f"{user_id}.jpg")
            with open(image_path, 'wb') as f: f.write(response.content)
            
            caption_data = post_data.get('onboardingCaption', {})
            caption_text = caption_data.get('caption', '')
            hashtags = caption_data.get('hashtags', '')
            full_caption = f"{caption_text}\n\n{hashtags}"
            
            cl.photo_upload(path=image_path, caption=full_caption)
            return True
        return False
    except Exception:
        traceback.print_exc()
        return False
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)