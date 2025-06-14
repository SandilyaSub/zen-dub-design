import os
import logging
import requests
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sarvam API key from environment
SARVAM_API_KEY = os.environ.get('SARVAM_API_KEY')

# Language code mapping
LANGUAGE_MAP = {
    'hindi': 'hi-IN',
    'english': 'en-IN',
    'telugu': 'te-IN',
    'tamil': 'ta-IN',
    'kannada': 'kn-IN',
    'gujarati': 'gu-IN',
    'marathi': 'mr-IN',
    'bengali': 'bn-IN',
    'odia': 'od-IN',
    'punjabi': 'pa-IN',
    'malayalam': 'ml-IN'
}

# Reverse mapping for converting API language codes to our format
REVERSE_LANGUAGE_MAP = {
    'hi-IN': 'hindi',
    'en-IN': 'english',
    'te-IN': 'telugu',
    'ta-IN': 'tamil',
    'kn-IN': 'kannada',
    'gu-IN': 'gujarati',
    'mr-IN': 'marathi',
    'bn-IN': 'bengali',
    'od-IN': 'odia',
    'pa-IN': 'punjabi',
    'ml-IN': 'malayalam'
}

def translate_text(text, source_lang, target_lang, mode="formal", speaker_gender="Female"):
    """
    Translate text from source language to target language using Sarvam API.
    
    Args:
        text: Text to translate
        source_lang: Source language code (e.g., 'hindi', 'english')
        target_lang: Target language code (e.g., 'hindi', 'english')
        mode: Translation mode (formal, modern-colloquial, classic-colloquial, code-mixed)
        speaker_gender: Gender of the speaker (Male, Female)
        
    Returns:
        translated_text: Translated text
    """
    try:
        logger.info(f"Translating from {source_lang} to {target_lang}")
        
        # Check for API key
        if not SARVAM_API_KEY:
            logger.error("No Sarvam API key found.")
            return "Error: No API key available for translation."
        
        # Convert language names to codes
        source_code = LANGUAGE_MAP.get(source_lang, source_lang)
        if source_code == source_lang and source_lang not in LANGUAGE_MAP.values():
            source_code = "auto"  # Use auto-detection if language is unknown
            
        target_code = LANGUAGE_MAP.get(target_lang, target_lang)
        if target_code == target_lang and target_lang not in LANGUAGE_MAP.values():
            logger.error(f"Unsupported target language: {target_lang}")
            return f"Error: Unsupported target language: {target_lang}"
        
        # Check if source and target are the same
        if source_code == target_code and source_code != "auto":
            logger.info("Source and target languages are the same, returning original text")
            return text
        
        # Prepare API request
        url = "https://api.sarvam.ai/translate"
        headers = {
            "API-Subscription-Key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text,
            "source_language_code": source_code,
            "target_language_code": target_code,
            "speaker_gender": speaker_gender,
            "mode": mode,
            "enable_preprocessing": True,
            "output_script": None,  # No transliteration applied, preserves business-specific words
            "numerals_format": "international"  # Use regular numerals (0-9)
        }
        
        # Make API request
        logger.info("Sending translation request to Sarvam API")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check for successful response
        if response.status_code == 200:
            result = response.json()
            
            # Extract translated text
            translated_text = result.get("translated_text", "")
            detected_source_lang = result.get("source_language_code", source_code)
            
            logger.info(f"Translation complete: {translated_text[:50]}...")
            logger.info(f"Detected source language: {detected_source_lang}")
            
            return translated_text
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            
            # Fall back to original text if API fails
            return f"Error: Translation service unavailable. Status code: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return f"Error: {str(e)}"  # Return error message on exception
