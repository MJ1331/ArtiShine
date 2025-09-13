import torch
from faster_whisper import WhisperModel
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global model loaded once at startup
model = None
device = "cuda" if torch.cuda.is_available() else "cpu"

def load_model(model_size: str = "medium", compute_type: str = "int8"):
    global model
    if model is None:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info(f"Model loaded on {device}")

def transcribe_audio(audio_file_path: str, lang: Optional[str] = None, task: str = "transcribe") -> Optional[str]:
    global model
    if model is None:
        load_model()  # Fallback load if not called at startup
    
    try:
        segments, _ = model.transcribe(
            audio_file_path, 
            language=lang, 
            task=task, 
            beam_size=5,
            condition_on_previous_text=False  
        )
        return " ".join(segment.text for segment in segments).strip()
    except ValueError as e:
        logger.error(f"Audio format error: {e}")
        return None
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None