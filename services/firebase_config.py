# services/firebase_config.py
import os
import firebase_admin
from firebase_admin import credentials, firestore, storage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

db = None
bucket = None

try:
    # Use the service account key file
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': os.getenv("FIREBASE_STORAGE_BUCKET")
    })
    
    db = firestore.client()
    bucket = storage.bucket()
    
    print("✅ Firebase initialized successfully.")

except Exception as e:
    print(f"🔥 Firebase initialization failed: {e}")
    print("Ensure 'serviceAccountKey.json' is in the root and .env is set.")