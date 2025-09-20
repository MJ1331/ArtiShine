# main.py
from fastapi import FastAPI
# UPDATED: Import from the new routes filename
from routes.insta_onboarding_routes import router as onboarding_router

app = FastAPI(
    title="Artishine Instagram Poster",
    description="An API to post an artisan's onboarding content to Instagram."
)

# Include the router from the routes file
app.include_router(onboarding_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Artishine Instagram Poster API. Go to /docs for the API documentation."}