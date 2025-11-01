# models/user_models.py
from pydantic import BaseModel, Field, EmailStr
from enum import Enum
from typing import Optional

class UserRole(str, Enum):
    ARTISAN = "artisan"
    BUYER = "buyer"

class ArtisanDetails(BaseModel):
    name: str = Field(..., description="Artisan's full name")
    email: EmailStr = Field(..., description="Artisan's email address")
    password: str = Field(..., description="Artisan's password (will be hashed)")
    role: UserRole = Field(default=UserRole.ARTISAN, description="User role (artisan or buyer)")
    place: str = Field(..., description="Location, e.g., 'Jaipur, India'")
    latitude: float = Field(..., description="Latitude coordinate of the location")
    longitude: float = Field(..., description="Longitude coordinate of the location")
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

class BuyerDetails(BaseModel):
    name: str = Field(..., description="Buyer's full name")
    email: EmailStr = Field(..., description="Buyer's email address")
    password: str = Field(..., description="Buyer's password (will be hashed)")
    role: UserRole = Field(default=UserRole.BUYER, description="User role (must be buyer)")
    place: str = Field(..., description="Location, e.g., 'Jaipur, India'")
    latitude: float = Field(..., description="Latitude coordinate of the location")
    longitude: float = Field(..., description="Longitude coordinate of the location")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")
    role: UserRole = Field(..., description="User role (artisan or buyer)")

class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated name")
    shop_name: Optional[str] = Field(None, alias="shopName", description="Updated shop name")
    place: Optional[str] = Field(None, alias="location", description="Updated location")
    bio: Optional[str] = Field(None, description="Updated bio")

    class Config:
        populate_by_name = True  # Allows using `shopName` in JSON, maps to `shop_name`