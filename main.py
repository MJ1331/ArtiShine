# main.py
import uvicorn
from fastapi import FastAPI
from routes import user_routes, product_routes, map_explore_routes, wishlist_routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="ArtiShine API 🚀",
    description="""
    Welcome to the ArtiShine API for the Google Hackathon.
    This API orchestrates the full artisan onboarding and product storytelling workflow.
    
    **Test the workflows:**
    1.  Go to `POST /users/register` to create a new artisan.
    2.  Go to `POST /products/create-product` to add a ¬new product for an artisan.
    """,
    version="1.0.0"
)

origins = [
    "http://localhost:5173",   # Vite dev server
    "http://127.0.0.1:5173",
    # add production origin(s) here, e.g. "https://app.example.com"
    "https://artisan-ai-backend.web.app"
    "https://artishine.in",                 # if frontend will use root later
    "https://api.artishine.in",             # allow api origin if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,           # or ["*"] for quick dev test (not for prod)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(
    user_routes.router,
    prefix="/users",
    tags=["1. User Routes"]
)
app.include_router(
    product_routes.router,
    prefix="/products",
    tags=["2. Product Routes"]
)
app.include_router(
    map_explore_routes.router,
    prefix="/map",
    tags=["3. Map & Explore Routes"]
)
app.include_router(
    wishlist_routes.router,
    prefix="/wishlists",
    tags=["4. Wishlist Routes"]
)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the ArtiShine API. Go to /docs to test the workflows."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)