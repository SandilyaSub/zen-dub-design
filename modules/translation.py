import os
import logging
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Language code mapping
LANGUAGE_MAP = {
    'hindi': 'hi',
    'english': 'en',
    'telugu': 'te',
    'tamil': 'ta',
    'kannada': 'kn',
    'gujarati': 'gu',
    'marathi': 'mr',
    'bengali': 'bn'
}

# API endpoint for translation
TRANSLATION_API_URL = "https://api-inference.huggingface.co/models/ai4bharat/indictrans2-indic-indic-1B"
TRANSLATION_API_KEY = os.environ.get("HF_API_KEY", "")

def translate_text(text, source_lang, target_lang):
    """
    Translate text from source language to target language.
    
    Args:
        text: Text to translate
        source_lang: Source language code (e.g., 'hindi', 'english')
        target_lang: Target language code (e.g., 'hindi', 'english')
        
    Returns:
        translated_text: Translated text
    """
    try:
        logger.info(f"Translating from {source_lang} to {target_lang}")
        
        # Convert language names to codes
        source_code = LANGUAGE_MAP.get(source_lang, source_lang)
        target_code = LANGUAGE_MAP.get(target_lang, target_lang)
        
        # Check if source and target are the same
        if source_code == target_code:
            logger.info("Source and target languages are the same, returning original text")
            return text
        
        # Prepare API request
        headers = {"Authorization": f"Bearer {TRANSLATION_API_KEY}"}
        payload = {
            "inputs": text,
            "parameters": {
                "src_lang": source_code,
                "tgt_lang": target_code
            }
        }
        
        # Make API request
        logger.info("Sending translation request to Hugging Face API")
        response = requests.post(TRANSLATION_API_URL, headers=headers, json=payload)
        
        # Check for successful response
        if response.status_code == 200:
            result = response.json()
            
            # Extract translated text
            if isinstance(result, list) and len(result) > 0:
                translated_text = result[0].get("translation_text", "")
            else:
                translated_text = result.get("translation_text", "")
                
            logger.info(f"Translation complete: {translated_text[:50]}...")
            return translated_text
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            
            # Fall back to original text if API fails
            return text
            
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return text  # Return original text on error
