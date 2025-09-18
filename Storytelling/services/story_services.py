# services/story_service.py

import base64
import logging
import os
import datetime
import json
import re
from typing import List, Dict

# Firebase & GCS
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud import storage

# LangChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

# --- Initializations ---
logger = logging.getLogger("storytelling_app")
db = firestore.client()
storage_client = storage.Client()
BUCKET_NAME = os.getenv("BUCKET_NAME")

llm = ChatOpenAI(
    model="google/gemini-flash-1.5",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=0.7,
    default_headers={
        "HTTP-Referer": "http://localhost",
        "X-Title": "Artisan Storytelling Service"
    }
)

# --- Helper Function ---
def parse_json_from_llm(raw_text: str) -> Dict:
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("Failed to parse extracted JSON from LLM output.")
            return {"error": "Failed to parse JSON from LLM output", "raw_output": raw_text}
    return {"error": "No JSON object found in LLM output", "raw_output": raw_text}

# --- Core Service Logic ---
def generate_story_from_details(details: Dict) -> Dict:
    """Generates a story by invoking the LLM with multimodal input."""
    try:
        audio_transcript = details["audio_transcript"]
        name = details["name"]
        shop_name = details["shop_name"]
        location = details["location"]
        base64_images = details["base64_images"]
    except KeyError as e:
        raise ValueError(f"Missing key in details dictionary: {e}")

    user_prompt_message = HumanMessage(
        content=[
            {"type": "text", "text": f"""
             Analyze the artisan's description and product images to generate a structured story.
             Artisan's Spoken Description: "{audio_transcript}"
             Artisan's Details: - Name: {name}, - Shop Name: {shop_name}, - Location: {location}
             Classify the product into one of these categories: Pottery, Painting, Food, Fabric and Clothing, Glass Artefact, Sculptures.
             Then, generate a JSON object with keys: "Title", "Category", "Tagline", "ForWhom", "Material", "Method", "CulturalSignificance", "WhoMadeIt".
             The story must be inspired by the visuals in the images.
             """},
            *[
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                for img_b64 in base64_images
            ],
        ]
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert cultural product storyteller. Your task is to visually analyze product images and combine that with an artisan's description to generate a compelling story. The final output must be a single, clean JSON object."),
        user_prompt_message
    ])
    chain = prompt | llm
    response = chain.invoke({})
    return parse_json_from_llm(response.content)


def save_story_to_gcs_and_firestore(final_data: Dict):
    """Saves the final story data to both GCS and Firestore."""
    user_id = final_data["user_id"]
    product_id = final_data["product_id"]

    # Save to Firestore
    product_ref = db.collection("product_stories").document(user_id).collection("products").document(product_id)
    product_ref.set(final_data, merge=True)

    # Save to GCS
    filename = f"{user_id}_{product_id}.json"
    blob = storage_client.bucket(BUCKET_NAME).blob(f"stories/{filename}")
    blob.upload_from_string(json.dumps(final_data, indent=2), content_type="application/json")
    logger.info(f"Story saved successfully for product {product_id}")