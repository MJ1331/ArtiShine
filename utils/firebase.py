import os
from firebase_admin import credentials, initialize_app, firestore, storage
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Global variables to track initialization (singleton pattern for clients)
_firebase_initialized = False
_db = None
_bucket = None

# Load environment variables
load_dotenv()
SERVICE_ACCOUNT_KEY_PATH = os.getenv("SERVICE_ACCOUNT_KEY_PATH")
if not SERVICE_ACCOUNT_KEY_PATH:
    raise ValueError("SERVICE_ACCOUNT_KEY_PATH environment variable not set.")

STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
if not STORAGE_BUCKET:
    raise ValueError("FIREBASE_STORAGE_BUCKET environment variable not set.")

# Initialize Firebase (called once in main.py)
def init_firebase():
    global _firebase_initialized, _db, _bucket
    if _firebase_initialized:
        logger.info("Firebase already initialized")
        return
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        initialize_app(cred, options={'storageBucket': STORAGE_BUCKET})
        _db = firestore.client()
        _bucket = storage.bucket()
        _firebase_initialized = True
        logger.info("Firebase initialized successfully")
    except Exception as e:
        logger.error(f"Firebase initialization error: {e}")
        raise

def get_db():
    global _db
    if not _firebase_initialized:
        raise ValueError("Firebase not initialized. Call init_firebase() first.")
    return _db


def get_firestore_client():
    global _db
    if not _firebase_initialized:
        raise ValueError("Firebase not initialized. Call init_firebase() first.")
    return _db

# Get Storage bucket (call after initialization)
def get_storage_bucket():
    global _bucket
    if not _firebase_initialized:
        raise ValueError("Firebase not initialized. Call init_firebase() first.")
    return _bucket

def get_bucket():
    global _bucket
    if not _firebase_initialized:
        raise ValueError("Firebase not initialized. Call init_firebase() first.")
    return _bucket