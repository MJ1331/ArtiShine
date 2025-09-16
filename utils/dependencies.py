from fastapi import HTTPException, Header, Depends
from firebase_admin import auth, firestore
from utils.firebase import get_db
import logging

logger = logging.getLogger(__name__)

async def get_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return authorization.split(" ")[1]

async def get_current_artisan(
    token: str = Depends(get_token),
    db: firestore.client = Depends(get_db)
):
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists or user_doc.to_dict().get('role') != 'artisan':
            raise HTTPException(status_code=403, detail="Artisan access required")
        return user_doc.to_dict(), uid
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")

async def get_current_buyer(
    token: str = Depends(get_token),
    db: firestore.client = Depends(get_db)
):
    try:
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        user_doc = db.collection('users').document(uid).get()
        if not user_doc.exists or user_doc.to_dict().get('role') != 'buyer':
            raise HTTPException(status_code=403, detail="Buyer access required")
        return user_doc.to_dict(), uid
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")