# services/insta_product_service.py

import os
import requests
import traceback
import tempfile
from dotenv import load_dotenv
from typing import List, Dict
from instagrapi import Client
from fastapi import UploadFile

# --- Firebase initialization ---
# Ensure you have firebase_admin installed: pip install firebase-admin
from firebase_admin import credentials, initialize_app, firestore

load_dotenv()
db = None
try:
    # Make sure your .env file has the correct path for SERVICE_ACCOUNT_KEY_PATH
    cred = credentials.Certificate(os.getenv('SERVICE_ACCOUNT_KEY_PATH'))
    initialize_app(cred)
    db = firestore.client()
    print("✅ Firebase initialized successfully in service layer.")
except Exception as e:
    print(f"🔥 Error initializing Firebase: {e}")
    print("Please ensure your .env file is set up correctly.")

# --- Core Functions ---

def get_product_story(user_id: str, product_id: str) -> Dict | None:
    """
    Fetches a product story from Firestore.
    Path: product_stories/{user_id}/products/{product_id}
    """
    if not db:
        print("Firestore client is not available.")
        return None
    try:
        doc_ref = db.collection('product_stories').document(user_id).collection('products').document(product_id)
        doc = doc_ref.get()
        if doc.exists:
            print(f"✅ Successfully found story for ProductID: {product_id}")
            return doc.to_dict()
        else:
            print(f"❌ No story found for UserID '{user_id}' and ProductID '{product_id}'")
            return None
    except Exception as e:
        print(f"🔥 Error getting product story: {str(e)}")
        return None

def format_story_caption(story_data: Dict) -> str:
    """Formats the fetched story data into a beautiful Instagram caption."""
    story = story_data.get('story', {})
    who_made_it = story.get('WhoMadeIt', {})
    
    caption_parts = [
        f"✨ {story.get('Title', 'Handcrafted Treasure')} ✨",
        f"\"{story.get('Tagline', '')}\"",
        "\n----------------------------------------\n",
        f"🎨 Category: {story.get('Category', 'Unique Art')}",
        f"🏺 Material: {story.get('Material', 'High-quality materials')}",
        f"🔨 Method: {story.get('Method', 'Created with passion and skill.')}",
        f"🌍 Cultural Significance: {story.get('CulturalSignificance', 'A piece rich in history and meaning.')}",
        f"🎁 Perfect For: {story.get('ForWhom', 'Art lovers and connoisseurs.')}",
        "\n----------------------------------------\n",
        f"👨‍🎨 Meet the Artisan: {who_made_it.get('Name', 'A talented local artisan')}",
        f"📍 From: {who_made_it.get('Location', 'A special place')}",
        f"🛍️ Shop: {who_made_it.get('ShopName', 'Our Artisan Marketplace')}",
        "\n#ArtisanMade #SupportLocalArtisans #Handcrafted #Storytelling #Artishine"
    ]
    
    return "\n".join(caption_parts)


async def post_story_to_instagram(caption: str, images: List[UploadFile]) -> bool:
    """
    Saves uploaded images temporarily and posts them to Instagram
    as a single photo or an album.
    """
    temp_dir = tempfile.mkdtemp()
    image_paths = []
    
    try:
        # Save uploaded files to the temporary directory
        for image in images:
            file_path = os.path.join(temp_dir, image.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(await image.read())
            image_paths.append(file_path)

        if not image_paths:
            print("❌ No images were provided to post.")
            return False

        # Login to Instagram
        cl = Client()
        cl.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
        print("✅ Successfully logged into Instagram.")

        # Upload based on the number of images
        if len(image_paths) == 1:
            print("📤 Uploading a single photo...")
            cl.photo_upload(path=image_paths[0], caption=caption)
        else:
            print(f"📤 Uploading an album with {len(image_paths)} photos...")
            cl.album_upload(paths=image_paths, caption=caption)
        
        print("✅ Successfully posted to Instagram!")
        return True

    except Exception as e:
        print(f"🔥 An error occurred while posting to Instagram: {e}")
        traceback.print_exc()
        return False
        
    finally:
        # Clean up: remove temporary files
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(temp_dir)
        print("🗑️ Temporary files cleaned up.")