# main.py

from dotenv import load_dotenv

# This MUST be the first line to ensure variables are loaded
load_dotenv()

from fastapi import FastAPI
from routes.onboarding_routes import router as onboarding_router

app = FastAPI(
    title="Artisan Onboarding Agent API",
    description="An API to generate welcome captions and images for new artisans.",
    version="2.0.0"
)

# Include the router from the routes file
app.include_router(onboarding_router)

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome! Visit /docs for the API documentation."}