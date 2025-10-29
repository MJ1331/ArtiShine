import os
import json
import base64
import requests
import mimetypes
import time  # <-- Make sure this import is at the top
from dotenv import load_dotenv

# --- NEW: Use the 'google-generativeai' library for API key access ---
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION")
API_KEY = os.getenv("GOOGLE_API_KEY") # <-- Get the API key

# --- Clients ---
text_model = None
vision_model = None
try:
    # --- 1. Vertex AI (Gemini) Client ---
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    genai.configure(api_key=API_KEY)

    # --- Your working model names ---
    # Model for text-only requests
    text_model = genai.GenerativeModel("gemini-2.5-flash")
    # Model for multimodal (text + image) requests
    vision_model = genai.GenerativeModel("gemini-2.5-flash")

    print("✅ Google AI Services (Gemini text & vision) initialized with API Key.")

except Exception as e:
    print(f"🔥 Google AI Services initialization failed: {e}")

# --- 1. Vertex AI (Gemini) ---

def generate_json_from_text_gcp(prompt: str) -> dict:
    """
    Generates a JSON response from a text prompt using the Gemini API key.
    Uses the text-only model 'gemini-pro'.
    """
    global text_model
    if not text_model:
        return {"error": "Gemini text model not initialized."}

    # Your print statement here still says "gemini-pro", you can update it if you want
    print("Generating text-to-JSON with Gemini API (gemini-2.5-flash)...") 
    try:
        config = genai.types.GenerationConfig(response_mime_type="application/json")

        # --- FIX: Use the 'text_model' ---
        response = text_model.generate_content(prompt, generation_config=config)

        # Check for empty or blocked response
        if not response.parts:
            print(f"🔥 Gemini API text generation returned empty response. Prompt: {prompt}")
            print(f"Full response object: {response}")
            # Check for safety ratings if available
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return {"error": f"Request blocked due to: {response.prompt_feedback.block_reason}"}
            return {"error": "Gemini API returned an empty response."}

        return json.loads(response.text)
    except Exception as e:
        print(f"🔥 Gemini API text generation failed: {e}")
        # Log the prompt that caused the error (optional, be careful with sensitive data)
        # print(f"Failed prompt: {prompt}")
        return {"error": str(e)}

def generate_json_from_multimodal_gcp(prompt: str, image_bytes_list: list) -> dict:
    """
    Generates a JSON response from text + images using the Gemini API key.
    Uses the multimodal model 'gemini-pro-vision'.
    """
    global vision_model
    if not vision_model:
        return {"error": "Gemini vision model not initialized."}

    # Your print statement here still says "gemini-pro-vision", you can update it
    print("Generating multimodal-to-JSON with Gemini API (gemini-2.5-flash)...")
    try:
        image_parts = []
        for img_bytes in image_bytes_list:
            # Simple mime-type detection for common formats
            if img_bytes.startswith(b'\xff\xd8'):
                mime_type = "image/jpeg"
            elif img_bytes.startswith(b'\x89PNG'):
                mime_type = "image/png"
            elif img_bytes.startswith(b'GIF8'):
                mime_type = "image/gif"
            elif img_bytes.startswith(b'RIFF') and img_bytes[8:12] == b'WEBP':
                mime_type = "image/webp" # Added WebP support
            else:
                mime_type = "image/jpeg" # Default or fallback

            image_parts.append({"mime_type": mime_type, "data": img_bytes})

        config = genai.types.GenerationConfig(response_mime_type="application/json")

        # --- FIX: Use the 'vision_model' ---
        # Ensure the prompt comes *before* the images for gemini-pro-vision
        content_parts = [prompt] + image_parts
        response = vision_model.generate_content(
            content_parts,
            generation_config=config
        )

        # Check for empty or blocked response
        if not response.parts:
            print(f"🔥 Gemini API multimodal generation returned empty response. Prompt: {prompt}")
            print(f"Full response object: {response}")
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return {"error": f"Request blocked due to: {response.prompt_feedback.block_reason}"}
            return {"error": "Gemini API returned an empty response."}

        return json.loads(response.text)
    except Exception as e:
        print(f"🔥 Gemini API multimodal generation failed: {e}")
        # print(f"Failed prompt: {prompt}") # Optional logging
        return {"error": str(e)}

# --- 2. Cloud Speech-to-Text (via REST API) ---

def transcribe_audio_gcp(gcs_uri: str, language_code: str, content_type: str) -> str:
    """
    Transcribes audio from a GCS URI using the SYNCHRONOUS REST API.
    This is the correct method for short audio files (<60 seconds).
    """
    if not API_KEY:
        print("🔥 API Key not configured for Speech-to-Text.")
        return ""

    print(f"Transcribing audio from {gcs_uri} with content type {content_type} (synchronous, latest_short model)...")

    # --- Use the 'recognize' (synchronous) endpoint ---
    url = f"https://speech.googleapis.com/v1p1beta1/speech:recognize?key={API_KEY}"

    # Dynamic Encoding Logic
    encoding = "ENCODING_UNSPECIFIED"
    if "mpeg" in content_type or "mp3" in content_type:
        encoding = "MP3"
    elif "wav" in content_type:
        encoding = "LINEAR16"
    elif "flac" in content_type:
        encoding = "FLAC"
    elif "ogg" in content_type:
        encoding = "OGG_OPUS"
    else:
        print(f"Warning: Unsupported audio type '{content_type}', trying ENCODING_UNSPECIFIED")

    # --- Speech Adaptation (for better accuracy on specific words) ---
    adaptation_config = {
        "phraseSets": [
            {
                "phrases": [
                    {"value": "குமார்", "boost": 20},       # Kumar
                    {"value": "சென்னை", "boost": 20},      # Chennai
                    {"value": "கை தொழில்", "boost": 20},    # Kai Thozhil (handicraft)
                    {"value": "மயில் பொம்மை", "boost": 20}, # Mayil Bommai (peacock doll)
                    {"value": "வறுமை", "boost": 15}       # Varumai (poverty)
                ]
            }
        ]
    }

    # --- **CORRECTED CONFIG** ---
    config = {
        "encoding": encoding,
        "languageCode": language_code,
        "model": "latest_short",  # <-- **FIX 1: Use 'latest_short' for clips < 60s**
        "enableAutomaticPunctuation": True,
        "useEnhanced": True,      # <-- Use enhanced model for better accuracy
        "adaptation": adaptation_config # <-- Add hints for the API
    }
    
    # --- **CRITICAL FIX 2: Add sampleRateHertz for MP3/FLAC** ---
    # We must provide a sample rate for these encodings, or the API returns '0s'
    if encoding in ["MP3", "LINEAR16", "FLAC"]:
        config["sampleRateHertz"] = 16000 

    payload = {
        "config": config,
        "audio": {
            "uri": gcs_uri
        }
    }

    try:
        # --- Make a single synchronous request (no polling) ---
        response = requests.post(url, json=payload)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        result = response.json()

        # Check if results are present and not empty
        if "results" in result and result["results"] and result["results"][0].get("alternatives"):
            # Join all transcript segments together
            full_transcript = " ".join(
                res["alternatives"][0].get("transcript", "")
                for res in result["results"]
                if res.get("alternatives")
            )
            return full_transcript.strip()
        else:
            print(f"No transcription results found or unexpected format. Response: {result}")
            return ""
            
    except requests.exceptions.RequestException as e:
        print(f"🔥 Cloud Speech-to-Text REST API failed: {e}")
        error_body = "No response body available."
        if e.response is not None:
            try:
                error_body = e.response.json() # Try parsing JSON error
            except json.JSONDecodeError:
                error_body = e.response.text # Fallback to raw text
        print(f"Response body: {error_body}")
        return ""

# --- 3. Cloud Translation (via REST API) ---

def translate_text_gcp(text: str, target_language: str = "en") -> str:
    """
    Translates text using the v2 REST API and an API key.
    """
    if not API_KEY:
        print("🔥 API Key not configured for Translation.")
        return ""
    if not text: # Handle empty input gracefully
        print("🔥 Translation input text is empty.")
        return ""

    print(f"Translating text to '{target_language}' via REST API...")

    # v2 REST API endpoint
    url = f"https://translation.googleapis.com/language/translate/v2?key={API_KEY}"

    payload = {
        "q": text,
        "target": target_language,
        "format": "text" # Explicitly request plain text translation
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()

        result = response.json()

        # Robust check for the translated text
        if (isinstance(result, dict) and
            "data" in result and
            isinstance(result["data"], dict) and
            "translations" in result["data"] and
            isinstance(result["data"]["translations"], list) and
            len(result["data"]["translations"]) > 0 and
            isinstance(result["data"]["translations"][0], dict) and
            "translatedText" in result["data"]["translations"][0]):
            return result["data"]["translations"][0]["translatedText"]
        else:
            print(f"Cloud Translation returned an unexpected-response format: {result}")
            return ""

    except requests.exceptions.RequestException as e:
        print(f"🔥 Cloud Translation REST API failed: {e}")
        error_body = "No response body available."
        if e.response is not None:
            try:
                error_body = e.response.json()
            except json.JSONDecodeError:
                error_body = e.response.text
        print(f"Response body: {error_body}")
        return ""