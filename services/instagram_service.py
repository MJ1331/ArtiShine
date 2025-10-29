import os
import os.path  # <-- ADDED THIS IMPORT
import requests
import traceback
import tempfile
from dotenv import load_dotenv
from typing import List, Dict
from instagrapi import Client

from .firebase_config import db

# Load .env variables
load_dotenv()

# --- ADDED THIS ---
# Define a path to store the session settings
IG_SETTINGS_PATH = "ig_settings.json"

# --- Helper: Get Onboarding Post Data ---
def _get_onboarding_post_data(user_id: str) -> dict | None:
    if not db:
        print("Firestore client is not available.")
        return None
    try:
        doc_ref = db.collection('Onboarding_Posts').document(user_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            print(f"No onboarding post found for UserID: {user_id}")
            return None
    except Exception as e:
        print(f"Error getting onboarding post: {str(e)}")
        return None

# --- Helper: Get Product Post Data ---
def _get_product_story_data(user_id: str, product_id: str) -> Dict | None:
    if not db:
        print("Firestore client is not available.")
        return None
    try:
        doc_ref = db.collection('product_stories').document(user_id).collection('products').document(product_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            return None
    except Exception as e:
        print(f"Error getting product story: {str(e)}")
        return None

# --- Helper: Format Product Caption ---
def _format_story_caption(story_data: Dict) -> str:
    # (This is your original formatting function)
    story = story_data.get('story', {})
    artisan = story_data.get('artisan_details', {})
    
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
        f"👨‍🎨 Meet the Artisan: {artisan.get('name', 'A talented local artisan')}",
        f"📍 From: {artisan.get('location', 'A special place')}",
        f"🛍️ Shop: {artisan.get('shop_name', 'Our Artisan Marketplace')}",
        "\n#ArtisanMade #SupportLocalArtisans #Handcrafted #Storytelling #Artishine"
    ]
    
    return "\n".join(caption_parts)

# --- Main Service Function 1: Post Onboarding ---
async def post_onboarding(user_id: str):
    print(f"Attempting to post onboarding for {user_id}")
    post_data = _get_onboarding_post_data(user_id)
    if not post_data:
        print(f"No onboarding data found to post for {user_id}.")
        return

    image_path = None
    temp_dir = tempfile.mkdtemp()
    
    try:
        cl = Client()

        # --- MODIFICATION: Add session caching ---
        if os.path.exists(IG_SETTINGS_PATH):
            print("Found Instagram settings. Loading session...")
            cl.load_settings(IG_SETTINGS_PATH)
            # Login again to verify session
            cl.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
        else:
            print("No Instagram settings found. Logging in for the first time...")
            cl.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
            print("Saving Instagram session settings...")
            cl.dump_settings(IG_SETTINGS_PATH)
        # --- END OF MODIFICATION ---

        img_url = post_data.get('onboardingImageUrl')
        if not img_url:
            print("No image URL in post data.")
            return

        response = requests.get(img_url)
        if response.status_code == 200:
            image_path = os.path.join(temp_dir, f"{user_id}.jpg")
            with open(image_path, 'wb') as f: f.write(response.content)
            
            # This logic now correctly formats the hashtag list
            caption_data = post_data.get('onboardingCaption', {})
            caption_text = caption_data.get('caption', '')
            hashtags_data = caption_data.get('hashtags')  # Get the raw hashtag data

            hashtag_string = "" # Default to an empty string

            if isinstance(hashtags_data, list):
                # AI gave a list: add '#' to each item and join them with a space
                hashtag_string = " ".join([f"#{tag.lstrip('#')}" for tag in hashtags_data])
            elif isinstance(hashtags_data, str):
                # AI gave a single string: use it as is
                hashtag_string = hashtags_data

            # This creates a clean caption
            full_caption = f"{caption_text}\n\n{hashtag_string}"
            
            cl.photo_upload(path=image_path, caption=full_caption)
            print(f"✅ Successfully posted onboarding for {user_id}")
        else:
            print(f"Failed to download image from {img_url}")
            
    except Exception:
        traceback.print_exc()
    finally:
        if image_path and os.path.exists(image_path):
            os.remove(image_path)
        os.rmdir(temp_dir)

# --- Main Service Function 2: Post Product ---
async def post_product(user_id: str, product_id: str):
    print(f"Attempting to post product {product_id} for {user_id}")
    story_data = _get_product_story_data(user_id, product_id)
    if not story_data:
        print(f"No product data found to post for {product_id}.")
        return

    caption = _format_story_caption(story_data)
    image_urls = story_data.get('image_urls', [])
    
    if not image_urls:
        print("No image URLs found in product data.")
        return

    temp_dir = tempfile.mkdtemp()
    image_paths = []

    try:
        # Download all images from GCS
        for i, url in enumerate(image_urls):
            response = requests.get(url)
            if response.status_code == 200:
                file_path = os.path.join(temp_dir, f"product_{i}.jpg")
                with open(file_path, "wb") as f:
                    f.write(response.content)
                image_paths.append(file_path)
        
        if not image_paths:
            print("Failed to download any images.")
            return

        # Login and post
        cl = Client()

        # --- MODIFICATION: Add session caching ---
        if os.path.exists(IG_SETTINGS_PATH):
            print("Found Instagram settings. Loading session...")
            cl.load_settings(IG_SETTINGS_PATH)
            # Login again to verify session
            cl.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
        else:
            print("No Instagram settings found. Logging in for the first time...")
            cl.login(os.getenv('INSTAGRAM_USERNAME'), os.getenv('INSTAGRAM_PASSWORD'))
            print("Saving Instagram session settings...")
            cl.dump_settings(IG_SETTINGS_PATH)
        # --- END OF MODIFICATION ---
        
        if len(image_paths) == 1:
            cl.photo_upload(path=image_paths[0], caption=caption)
        else:
            cl.album_upload(paths=image_paths, caption=caption)
        
        print(f"✅ Successfully posted product {product_id}")

    except Exception:
        traceback.print_exc()
    finally:
        # Clean up
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
        os.rmdir(temp_dir)