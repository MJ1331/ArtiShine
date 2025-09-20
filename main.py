# main.py

from fastapi import FastAPI
# Import the router from your routes file
from routes.insta_product_routes import router as product_router

app = FastAPI(
    title="Artishine Product Story Poster",
    description="An API to fetch product stories and post them to Instagram.",
    version="1.0.0"
)

# Include the router from the routes file
app.include_router(product_router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Artishine API. Go to /docs for documentation."}