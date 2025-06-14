import os
import logging
import numpy as np
from pathlib import Path
import requests
import json
import tempfile
import base64  # For encoding audio data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Hugging Face API key from environment
HF_API_KEY = os.environ.get('HF_API_KEY')

def detect_language(audio_path):
    """
    Detect the language of the audio file using Hugging Face API.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        language: Detected language code (e.g., 'hindi', 'english')
    """
    try:
        logger.info(f"Detecting language for {audio_path}")
        
        # Default to English if API call fails
        if not HF_API_KEY:
            logger.warning("No Hugging Face API key found. Defaulting to English.")
            return "english"
        
        # Read audio file directly
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        # API call to Hugging Face for language detection
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}"
        }
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo",
            headers=headers,
            data=audio_data
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.text}")
            return "english"
        
        result = response.json()
        
        # Extract detected language
        detected_lang = result.get("language", "en")
        
        # Map language codes to our format
        lang_map = {
            "hi": "hindi",
            "en": "english",
            "te": "telugu",
            "ta": "tamil",
            "kn": "kannada",
            "gu": "gujarati",
            "mr": "marathi",
            "bn": "bengali"
        }
        
        language = lang_map.get(detected_lang, "english")
        logger.info(f"Detected language: {language}")
        
        return language
        
    except Exception as e:
        logger.error(f"Error detecting language: {e}")
        return "english"  # Default to English on error

def transcribe_audio(audio_path, language=None):
    """
    Transcribe audio to text using Hugging Face API.
    
    Args:
        audio_path: Path to the audio file
        language: Language of the audio (optional)
        
    Returns:
        text: Transcribed text
    """
    try:
        logger.info(f"Transcribing audio: {audio_path}")
        
        # Check for API key
        if not HF_API_KEY:
            logger.error("No Hugging Face API key found.")
            return "Error: No API key available for transcription."
        
        # Map language to Whisper format if provided
        lang_map = {
            "hindi": "hi",
            "english": "en",
            "telugu": "te",
            "tamil": "ta",
            "kannada": "kn",
            "gujarati": "gu",
            "marathi": "mr",
            "bengali": "bn"
        }
        
        # Read audio file directly
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        
        # API call to Hugging Face for transcription
        headers = {
            "Authorization": f"Bearer {HF_API_KEY}"
        }
        
        payload = {}
        if language and language in lang_map:
            payload["language"] = lang_map[language]
        
        response = requests.post(
            "https://api-inference.huggingface.co/models/openai/whisper-small",
            headers=headers,
            data=audio_data,
            params=payload
        )
        
        if response.status_code != 200:
            logger.error(f"API error: {response.text}")
            return "Error: Transcription service unavailable."
        
        result = response.json()
        
        # Extract transcribed text
        text = result.get("text", "").strip()
        
        logger.info(f"Transcription complete: {text[:50]}...")
        return text
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return "Error: Failed to transcribe audio."
