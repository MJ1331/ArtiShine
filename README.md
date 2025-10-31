# ArtiShine API

A comprehensive API for the ArtiShine platform that connects artisans with buyers through AI-powered product storytelling and social media integration.

## Overview

ArtiShine is a platform that empowers artisans by providing them with AI-generated product stories, automated Instagram posting, and a marketplace for buyers to discover authentic handmade crafts.

## Features

- **Dual User Roles**: Support for both artisans and buyers
- **AI-Powered Content**: Google Gemini AI for product story generation
- **Social Media Integration**: Automated Instagram posting
- **Location-Based Services**: Geographic coordinates for enhanced discovery
- **JWT Authentication**: Secure token-based authentication
- **Multi-Modal AI**: Text and image analysis for product storytelling

## API Endpoints

### Authentication

#### POST `/users/login`
Authenticate a user (artisan or buyer) and receive a JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "artisan" // or "buyer"
}
```

**Response:**
```json
{
  "message": "Login successful.",
  "user_id": "uuid-here",
  "role": "artisan",
  "token": "jwt-token-here",
  "token_type": "bearer"
}
```

### Artisan Management

#### POST `/users/register`
Register a new artisan with full onboarding workflow.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure123",
  "role": "artisan",
  "place": "Jaipur, India",
  "latitude": 26.9124,
  "longitude": 75.7873,
  "language": "hi-IN",
  "date_of_birth": "25-10-1985",
  "shop_name": "John's Pottery",
  "shop_type": "Pottery",
  "phone_number": "+91-9876543210"
}
```

**Response:** Artisan registration with onboarding post details and user_id.

#### GET `/users/`
Get all registered artisans (admin endpoint).

**Response:**
```json
{
  "total_artisans": 5,
  "artisans": [...]
}
```

#### GET `/users/me`
Get the authenticated artisan's profile.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:** Complete artisan profile data.

#### GET `/users/{user_id}`
Get a specific artisan's details by user_id.

**Response:** Artisan profile data.

### Buyer Management

#### POST `/users/register-buyer`
Register a new buyer.

**Request Body:**
```json
{
  "name": "Jane Smith",
  "email": "jane@example.com",
  "password": "buyer123",
  "role": "buyer",
  "place": "Mumbai, India",
  "latitude": 19.0760,
  "longitude": 72.8777
}
```

**Response:**
```json
{
  "message": "Buyer registered successfully.",
  "user_id": "uuid-here",
  "role": "buyer"
}
```

#### GET `/users/buyers`
Get all registered buyers (admin endpoint).

**Response:**
```json
{
  "total_buyers": 10,
  "buyers": [...]
}
```

#### GET `/users/buyers/me`
Get the authenticated buyer's profile.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:** Complete buyer profile data.

#### GET `/users/buyers/{user_id}`
Get a specific buyer's details by user_id.

**Response:** Buyer profile data.

### Product Management

#### POST `/products/create-product`
Create a new product for the authenticated artisan.

**Headers:** `Authorization: Bearer <jwt-token>`

**Form Data:**
- `images`: 1-4 product images (files)
- `voice_file`: Audio file describing the product (file)

**Process:**
1. Upload images and voice file to Google Cloud Storage
2. Transcribe voice using Google Speech-to-Text
3. Translate transcription to English
4. Generate product story using Google Gemini AI (text + images)
5. Auto-post to Instagram
6. Store product data in Firestore

**Response:** Complete product data with story and metadata.

#### GET `/products/`
Get all products from all artisans (admin endpoint).

**Response:**
```json
{
  "total_products": 25,
  "products": [...]
}
```

#### GET `/products/my-products`
Get all products for the authenticated artisan.

**Headers:** `Authorization: Bearer <jwt-token>`

**Response:**
```json
{
  "user_id": "artisan-uuid",
  "total_products": 3,
  "products": [...]
}
```

### Root Endpoint

#### GET `/`
API information and testing guide.

**Response:** Welcome message with testing instructions.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

Tokens expire after 24 hours and contain user information including role for access control.

## User Roles

### Artisan
- Full platform access
- Product creation and management
- Instagram posting integration
- Complete profile with business details

### Buyer
- Marketplace access
- Profile management
- Location-based discovery
- Streamlined registration

## Data Models

### ArtisanDetails
```json
{
  "name": "string",
  "email": "email",
  "password": "string",
  "role": "artisan",
  "place": "string",
  "latitude": "float",
  "longitude": "float",
  "language": "string",
  "date_of_birth": "string",
  "shop_name": "string",
  "shop_type": "string",
  "phone_number": "string"
}
```

### BuyerDetails
```json
{
  "name": "string",
  "email": "email",
  "password": "string",
  "role": "buyer",
  "place": "string",
  "latitude": "float",
  "longitude": "float"
}
```

## AI Services Integration

- **Google Gemini AI**: Product story generation from text and images
- **Google Speech-to-Text**: Voice transcription with language support
- **Google Translation**: Multi-language support
- **Instagram Graph API**: Automated social media posting

## Database Schema

### Collections
- `artisans`: Artisan user profiles
- `buyers`: Buyer user profiles
- `products_stories/{user_id}/products`: Product data organized by artisan
- `Onboarding_Posts`: Instagram onboarding posts

## Error Handling

The API provides comprehensive error handling with appropriate HTTP status codes:

- `200`: Success
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (insufficient permissions)
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Getting Started

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup:**
   - Configure Firebase credentials
   - Set up Google Cloud API keys
   - Configure Instagram credentials
   - Set JWT secret key

3. **Run the Server:**
   ```bash
   python main.py
   ```

4. **Access API Documentation:**
   Visit `http://localhost:8000/docs` for interactive API documentation.

## Testing the Workflows

1. Register an artisan: `POST /users/register`
2. Login as artisan: `POST /users/login`
3. Create a product: `POST /products/create-product`
4. View artisan profile: `GET /users/me`
5. View products: `GET /products/my-products`

## Security Features

- Password hashing with bcrypt
- JWT token authentication
- Role-based access control
- Input validation with Pydantic
- Secure file upload handling

## Technologies Used

- **FastAPI**: Modern Python web framework
- **Firebase**: Database and file storage
- **Google Cloud AI**: AI and ML services
- **Instagram API**: Social media integration
- **Pydantic**: Data validation
- **JWT**: Token-based authentication
- **bcrypt**: Password hashing