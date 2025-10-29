# main.py
import uvicorn
from fastapi import FastAPI
from routes import user_routes, product_routes

app = FastAPI(
    title="ArtiShine API 🚀",
    description="""
    Welcome to the ArtiShine API for the Google Hackathon.
    This API orchestrates the full artisan onboarding and product storytelling workflow.
    
    **Test the workflows:**
    1.  Go to `POST /users/register` to create a new artisan.
    2.  Go to `POST /products/create-product` to add a new product for an artisan.
    """,
    version="1.0.0"
)

# Include the routers
app.include_router(
    user_routes.router, 
    prefix="/users", 
    tags=["1. User Onboarding Workflow"]
)
app.include_router(
    product_routes.router, 
    prefix="/products", 
    tags=["2. New Product Workflow"]
)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the ArtiShine API. Go to /docs to test the workflows."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)