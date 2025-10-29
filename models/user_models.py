# models/user_models.py
from pydantic import BaseModel, Field

class ArtisanDetails(BaseModel):
    name: str = Field(..., description="Artisan's full name")
    place: str = Field(..., description="Location, e.g., 'Jaipur, India'")
    language: str = Field(..., 
        description="BCP-47 language code for speech-to-text, e.g., 'en-US' or 'hi-IN'",
        example="hi-IN"
    )
    date_of_birth: str = Field(..., 
        description="Date of birth in DD-MM-YYYY format",
        example="25-10-1985"
    )
    shop_name: str = Field(..., description="Name of the artisan's shop")
    shop_type: str = Field(..., description="Type of shop, e.g., 'Pottery', 'Textiles'")
    phone_number: str = Field(..., description="Artisan's phone number")