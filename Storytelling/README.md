# Artisan Storytelling API

This project is a FastAPI-powered API that generates rich, compelling stories for artisan products. It uses a multimodal AI model via OpenRouter to analyze product images and an artisan's spoken description, creating a structured story ready for an e-commerce platform.

## 📌 Features

-   **Multimodal Input**: Generates stories from both text (`audio_transcript`) and up to 5 product images.
-   **Data Integration**: Fetches artisan details (name, shop name, location) from Firestore to provide context to the AI.
-   **Structured JSON Output**: The AI returns a clean JSON object with fields like `Title`, `Category`, `Tagline`, and `CulturalSignificance`.
-   **Persistent Storage**: Saves the final generated story to a `product_stories` collection in Firestore and as a JSON file in Google Cloud Storage.
-   **High-Performance Backend**: Built with FastAPI for a fast and modern API experience.

---

## 🛠️ Technology Stack

-   **Backend**: FastAPI, Uvicorn
-   **AI**: LangChain with OpenRouter (using `google/gemini-flash-1.5`)
-   **Database**: Google Firestore
-   **Storage**: Google Cloud Storage
-   **Environment**: Python 3.10+

---

## 🚀 Setup & Installation

Follow these steps to get the project running locally.

### 1. Prerequisites

-   Python 3.10 or higher
-   A Google Cloud project with Firestore and Cloud Storage enabled.
-   An OpenRouter API Key.

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd storytelling-api # or your project folder name
```

### 3. Set Up a Virtual Environment

It's highly recommended to use a virtual environment.

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

Create a `requirements.txt` file with the content below and then install it.

**`requirements.txt`**:
```
fastapi
uvicorn[standard]
python-dotenv
firebase-admin
google-cloud-storage
langchain
langchain-core
langchain-openai
python-multipart
```

**Install Command**:
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a file named `.env` in the root of your project and add your credentials.

**`.env`**:
```
OPENROUTER_API_KEY="sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx"
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/serviceAccountKey.json"
BUCKET_NAME="your-gcs-bucket-name"
```

### 6. Add Google Cloud Credentials

Download your `serviceAccountKey.json` file from your Google Cloud project and place it in the location you specified in the `.env` file.

---

## ▶️ Running the Application

With the setup complete, run the following command in your terminal from the project's root directory:

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`, and the interactive documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.

---

## 📦 API Endpoint

### Generate a Story

-   **URL**: `/generate-story/`
-   **Method**: `POST`
-   **Content-Type**: `multipart/form-data`

#### Form Data:

| Parameter          | Type     | Description                                |
| ------------------ | -------- | ------------------------------------------ |
| `user_id`          | `string` | The ID of the artisan from your `artisans` collection. |
| `product_id`       | `string` | The unique ID for the product.             |
| `audio_transcript` | `string` | The text transcribed from the artisan's audio. |
| `images`           | `file[]` | Up to 5 image files of the product.        |

#### Example cURL Request:

```bash
curl -X 'POST' \
  '[http://127.0.0.1:8000/generate-story/](http://127.0.0.1:8000/generate-story/)' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'user_id=GW63g2APnuHQw3GkPa2z' \
  -F 'product_id=528326' \
  -F 'audio_transcript=This is a handmade clay pot, crafted with traditional techniques passed down in my family.' \
  -F 'images=@path/to/your/image.jpg;type=image/jpeg'
```