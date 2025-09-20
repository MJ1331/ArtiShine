# services/onboarding_service.py

import os
import datetime
import json
import uuid
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from typing import Dict
from fastapi import HTTPException
from pydantic import BaseModel, Field

# Firebase Admin SDK Imports
import firebase_admin
from firebase_admin import credentials, firestore, storage

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import tool, create_react_agent, AgentExecutor
from langchain import hub

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
llm = None
agent_executor = None

# --- Agent Tools ---
@tool
def get_welcome_caption(artisan_details: str) -> Dict:
    """Generates a social media caption."""
    global llm # Ensure tool can access the global llm
    try:
        parts = [item.strip() for item in artisan_details.split(',')]
        if len(parts) < 4:
            raise ValueError("Input string has fewer than 4 comma-separated parts.")
        name, dob_str, shop_name = parts[0], parts[1], parts[2]
        location = ", ".join(parts[3:])
    except ValueError as e:
        return {"error": f"Input format error: {e}"}

    # THIS IS THE CORRECT, FULL PROMPT
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are an expert content creator for ArtiShine. Return a clean JSON object with 'caption' and 'hashtags' keys."),
        ("user", f"Create a warm welcome caption for our platform. Introduce the artisan, {name}, and their shop, {shop_name}, located in {location}. It's important to feature the artisan's name prominently in the welcome message.")
    ])

    try:
        chain = prompt_template | llm
        response = chain.invoke({"name": name, "shop_name": shop_name, "location": location})
        return json.loads(response.content)
    except Exception as e:
        return {"error": f"Failed to generate caption: {e}"}

@tool
def generate_and_upload_onboarding_image(artisan_details_with_userid: str) -> str:
    """Generates and uploads an onboarding image."""
    global db, bucket # Ensure tool can access global db and bucket
    if not bucket or not db:
        return "Error: Firebase is not properly initialized."
    try:
        parts = [item.strip() for item in artisan_details_with_userid.split(',')]
        if len(parts) < 5:
            raise ValueError("Input string has fewer than 5 comma-separated parts.")
        user_id, name, dob_str, shop_name = parts[0], parts[1], parts[2], parts[3]
        location = ", ".join(parts[4:])
    except ValueError as e:
        return f"Input format error: {e}"

    try:
        image_path = r"./ARTISHIINE.png"
        font_path = r"./Pixel Game.otf"
        image = Image.open(image_path).convert('RGB')
        draw = ImageDraw.Draw(image)
        dob = datetime.datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = datetime.date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        lines = [("INTRODUCING","",250,30,False),("ARTISAN","",250,0,False),("",name,180,20,True),("Shop : ",shop_name,120,50,True),("Location : ",location,120,60,True),("Age : ",f"{age} years",120,0,False)]
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
        image_url = blob.public_url

        doc_ref = db.collection('Onboarding_Posts').document(user_id)
        doc_ref.set({'UserID': user_id, 'onboardingImageUrl': image_url}, merge=True)
        return f"Successfully generated and uploaded image. URL: {image_url}"
    except Exception as e:
        return f"Image generation or upload failed: {e}"

# --- Initialization Block ---
def initialize():
    global db, bucket, llm, agent_executor

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

    llm = ChatOpenAI(
        model="deepseek/deepseek-chat-v3.1:free",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        default_headers={ "HTTP-Referer": "http://localhost", "X-Title": "Artisan Onboarding API" }
    )

    tools = [get_welcome_caption, generate_and_upload_onboarding_image]
    prompt = hub.pull("hwchase17/react")
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent, tools=tools, verbose=True, 
        handle_parsing_errors=True, return_intermediate_steps=True
    )

initialize()

# --- Service Class ---
class OnboardingService:
    async def create_onboarding_post(self, details: ArtisanID) -> OnboardingOutput:
        if not db or not bucket:
            raise HTTPException(status_code=500, detail="Firebase is not initialized.")
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
            raise http_exc
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch or process artisan data: {str(e)}")

        agent_input = (
            f"First, create a welcome caption for an artisan using these details: "
            f"'{name}, {dob_string}, {shop_name}, {location}'. "
            f"Second, generate and upload an onboarding image using these details: "
            f"'{details.UserID}, {name}, {dob_string}, {shop_name}, {location}'."
        )
        try:
            response = await agent_executor.ainvoke({"input": agent_input})

            caption_data = None
            for step in reversed(response.get('intermediate_steps', [])):
                action, observation = step
                if action.tool == 'get_welcome_caption' and isinstance(observation, dict) and 'error' not in observation:
                    caption_data = observation
                    break
            
            if not caption_data:
                raise HTTPException(status_code=500, detail=f"Caption generation failed. The agent's last observation was: {response.get('intermediate_steps', [])[-1][1] if response.get('intermediate_steps') else 'None'}")
            
            user_doc = db.collection('Onboarding_Posts').document(details.UserID).get()
            if not user_doc.exists or 'onboardingImageUrl' not in user_doc.to_dict():
                raise HTTPException(status_code=404, detail="Image URL not found in Firestore.")
            
            image_url = user_doc.to_dict()['onboardingImageUrl']
            
            db.collection('Onboarding_Posts').document(details.UserID).set({
                'onboardingCaption': caption_data
            }, merge=True)

            return OnboardingOutput(
                UserID=details.UserID,
                CaptionData=caption_data,
                ImageURL=image_url
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))