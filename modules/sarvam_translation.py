"""
Sarvam Translation module using Sarvam-m Chat Completions API for diarized translation.
"""
import os
import json
import logging
import datetime
import requests
from typing import Dict, List, Any, Tuple, Optional
import copy

# Import Secret Manager utility
from utils.secret_manager import get_secret

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to get Sarvam API key from Secret Manager or environment variables
def get_sarvam_api_key():
    """Get the Sarvam API key from Secret Manager or environment variables."""
    api_key = get_secret("sarvam-api-key") or os.environ.get('SARVAM_API_KEY')
    if api_key:
        logger.info(f"API key is present with length: {len(api_key)}")
        logger.info(f"First 4 chars of API key: {api_key[:4]}")
        # Validate that it's not a placeholder value
        if api_key.startswith("your") or api_key == "placeholder" or api_key == "your-api-key-here":
            logger.error(f"Invalid Sarvam API key detected: {api_key}")
            return None
    else:
        logger.error("Failed to retrieve Sarvam API key")
    return api_key

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
REVERSE_LANGUAGE_MAP = {v: k for k, v in LANGUAGE_MAP.items()}

def extract_json_from_response(response_text: str) -> str:
    """
    Extract JSON from response text that might be wrapped in markdown code blocks
    
    Args:
        response_text: The raw response text from the model
        
    Returns:
        Extracted JSON string
    """
    if "```json" in response_text:
        return response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        return response_text.split("```")[1].split("```")[0].strip()
    return response_text.strip()

def is_valid_diarization_json(response_text: str) -> Tuple[bool, str]:
    """
    Validate if the response is a valid diarization JSON
    
    Args:
        response_text: Response text to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try to extract JSON if it's wrapped in markdown code blocks
        json_text = extract_json_from_response(response_text)
        
        # Parse the JSON
        data = json.loads(json_text)
        
        # Check for required fields
        if "transcript" not in data:
            return False, "Missing 'transcript' field"
        
        if "segments" not in data:
            return False, "Missing 'segments' field"
        
        if not isinstance(data["segments"], list):
            return False, "'segments' is not a list"
        
        # Check each segment
        for i, segment in enumerate(data["segments"]):
            if not isinstance(segment, dict):
                return False, f"Segment {i} is not an object"
            
            if "text" not in segment:
                return False, f"Segment {i} missing 'text' field"
        
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"Failed to parse as JSON: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

def translate_with_validation(input_json: Dict, system_prompt: str, max_retries: int = 2, api_key: str = None) -> Dict:
    """
    Translate with validation and retry logic using Sarvam Chat Completions API
    
    Args:
        input_json: The input JSON to translate
        system_prompt: The system prompt for translation
        max_retries: Maximum number of retries (default: 2)
        api_key: Sarvam API key (optional)
        
    Returns:
        Translated JSON data
        
    Raises:
        ValueError: If all translation attempts fail
    """
    attempts = 0
    last_error = ""
    
    # Get API key if not provided
    sarvam_api_key = api_key or get_sarvam_api_key()
    if not sarvam_api_key:
        raise ValueError("No Sarvam API key available")
    
    # Extract segments for translation
    segments = input_json.get("segments", [])
    if not segments:
        logger.warning("No segments found in input data")
        return input_json
    
    # Create a copy of the input JSON to modify
    translated_data = copy.deepcopy(input_json)
    translated_segments = []
    
    # Process each segment individually (Google-style)
    for segment in segments:
        segment_text = segment.get("text", "")
        if not segment_text:
            # Skip empty segments
            translated_segments.append(segment)
            continue
        
        # Try to translate this segment
        segment_attempts = 0
        while segment_attempts <= max_retries:
            try:
                # Prepare API request
                url = "https://api.sarvam.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {sarvam_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Format messages for chat completions API - using Google's approach
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": segment_text}
                ]
                
                payload = {
                    "model": "sarvam-m",
                    "messages": messages,
                    "temperature": 0.2,  # Lower temperature for more consistent translations
                    "max_tokens": 2048
                }
                
                # Make API request
                logger.info(f"Translating segment {segment.get('segment_id', 'unknown')} (attempt {segment_attempts+1}/{max_retries+1})")
                response = requests.post(url, headers=headers, json=payload)
                
                # Check for successful response
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # Log raw response for debugging
                    logger.info(f"Received translation: {translated_text[:50]}...")
                    
                    # Create a new segment with the translated text
                    translated_segment = copy.deepcopy(segment)
                    translated_segment["text"] = translated_text
                    translated_segments.append(translated_segment)
                    break  # Success, move to next segment
                else:
                    error_msg = f"API request failed with status code {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    last_error = error_msg
                    segment_attempts += 1
                    if segment_attempts > max_retries:
                        # Use original text if all attempts fail
                        translated_segment = copy.deepcopy(segment)
                        translated_segment["translation_error"] = error_msg
                        translated_segments.append(translated_segment)
                        break
                    
            except Exception as e:
                error_msg = f"Error translating segment {segment.get('segment_id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                last_error = error_msg
                segment_attempts += 1
                if segment_attempts > max_retries:
                    # Use original text if all attempts fail
                    translated_segment = copy.deepcopy(segment)
                    translated_segment["translation_error"] = error_msg
                    translated_segments.append(translated_segment)
                    break
    
    # Update the translated data with the translated segments
    translated_data["segments"] = translated_segments
    
    # Create a transcript from all translated segments
    transcript = " ".join([s.get("text", "") for s in translated_segments])
    translated_data["transcript"] = transcript
    
    return translated_data

def create_translation_prompt(source_lang: str, target_lang: str) -> str:
    """
    Create a system prompt for translation using Google's exact prompt structure
    
    Args:
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        str: System prompt for translation
    """
    # Use the exact same system prompt structure as Google's translation module
    system_prompt = f"""You are a world-class multilingual translator. Your task is to translate from {source_lang} to {target_lang}.

TRANSLATION TASK:
Translate the following text, maintaining the original meaning, tone, and context.

RESPONSE FORMAT:
Return ONLY the translated text without any explanation or formatting.
"""
    
    return system_prompt

def translate_diarized_content(diarization_data, target_language: str, source_language: str = "auto", api_key: str = None):
    """
    Translate diarized content using Sarvam Chat Completions API with Google-style approach
    
    Args:
        diarization_data: Either a dictionary containing segments to translate or a list of texts
        target_language: Target language for translation
        source_language: Source language (default: auto-detect)
        api_key: Sarvam API key (optional)
        
    Returns:
        If input is a dictionary: Translated diarization data
        If input is a list: List of translated texts
        
    Raises:
        ValueError: If translation fails after retries
    """
    # Add explicit debug logging
    logger.info(f"Starting translate_diarized_content for target_language={target_language}, source_language={source_language}")
    
    # Get API key
    sarvam_api_key = api_key or get_sarvam_api_key()
    if not sarvam_api_key:
        error_msg = "Failed to retrieve Sarvam API key"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"SARVAM_API_KEY found with length: {len(sarvam_api_key)}")
    
    # Handle list input (simple text translation)
    if isinstance(diarization_data, list):
        logger.info(f"Translating list of {len(diarization_data)} texts")
        return [translate_text(text, target_language, source_language, sarvam_api_key) for text in diarization_data]
    
    # Handle dictionary input (diarization data)
    logger.info(f"Translating diarized content to {target_language}")
    
    # Make a copy to avoid modifying the original
    diarization_copy = copy.deepcopy(diarization_data)
    
    # Create system prompt for translation
    system_prompt = create_translation_prompt(source_language, target_language)
    
    # Process segments with context (Google-style)
    try:
        # Get all segments
        all_segments = diarization_copy.get("segments", [])
        if not all_segments:
            logger.warning("No segments found in diarization data")
            return diarization_copy
        
        logger.info(f"Found {len(all_segments)} segments to translate")
        
        # Add metadata for tracking
        if "metadata" not in diarization_copy:
            diarization_copy["metadata"] = {}
            
        diarization_copy["metadata"]["translation"] = {
            "source_language": source_language,
            "target_language": target_language,
            "timestamp": datetime.datetime.now().isoformat(),
            "translator": "sarvam_chat_api",
            "model": "sarvam-m"
        }
        
        # Translate the content using the Google-style approach
        translated_data = translate_with_validation(diarization_copy, system_prompt, api_key=sarvam_api_key)
        
        # Add translated_text field to each segment for compatibility
        for segment in translated_data.get("segments", []):
            if "translated_text" not in segment and "text" in segment:
                segment["translated_text"] = segment["text"]
        
        return translated_data
        
    except Exception as e:
        error_msg = f"Error translating diarized content: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def translate_text(text: str, target_lang: str, source_lang: str = "auto", api_key: str = None) -> str:
    """
    Translate text using Sarvam Chat Completions API.
    
    Args:
        text: Text to translate
        target_lang: Target language
        source_lang: Source language (default: auto-detect)
        api_key: Sarvam API key (optional)
        
    Returns:
        Translated text
    """
    try:
        logger.info(f"Translating text from {source_lang} to {target_lang}")
        
        # Get API key if not provided
        sarvam_api_key = api_key or get_sarvam_api_key()
        if not sarvam_api_key:
            logger.error("No Sarvam API key available")
            return "Error: No API key available for translation."
        
        # Create a simple input for the translation
        input_data = {
            "text": text
        }
        
        # Create system prompt for translation
        system_prompt = f"""You are a world-class multilingual translator. Your task is to translate from {source_lang} to {target_lang}.

TRANSLATION TASK:
Translate the following text, maintaining the original meaning, tone, and context:
"{text}"

RESPONSE FORMAT:
Return ONLY the translated text without any explanation or formatting.
"""
        
        # Prepare API request
        url = "https://api.sarvam.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {sarvam_api_key}",
            "Content-Type": "application/json"
        }
        
        # Format messages for chat completions API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        payload = {
            "model": "sarvam-m",
            "messages": messages,
            "temperature": 0.2,  # Lower temperature for more consistent translations
            "max_tokens": 2048
        }
        
        # Make API request
        logger.info("Sending translation request to Sarvam Chat API")
        response = requests.post(url, headers=headers, json=payload)
        
        # Check for successful response
        if response.status_code == 200:
            result = response.json()
            translated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            logger.info(f"Translation complete: {translated_text[:50]}...")
            return translated_text
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return f"Error: Translation service unavailable. Status code: {response.status_code}"
            
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        return f"Error: {str(e)}"  # Return error message on exception

# For backward compatibility
sarvam_translate_diarized_content = translate_diarized_content

def sarvam_back_translate(translated_text, original_source_lang, target_lang, api_key=None):
    """
    Perform back-translation using Sarvam AI.
    
    Args:
        translated_text: Text that has been translated to target_lang
        original_source_lang: Original source language
        target_lang: Current language of the translated_text
        api_key: Sarvam API key (overrides environment variable)
        
    Returns:
        Back-translated text in the original source language
    """
    print(f"==== SARVAM TRANSLATION DEBUG ==== Performing back-translation from {target_lang} to {original_source_lang}")
    
    # Simply reverse the direction of translation
    back_translated_text = translate_text(
        translated_text,
        target_lang,  # Now this is the source
        original_source_lang,  # Now this is the target
        mode="modern-colloquial",  # Use colloquial mode to preserve English terms
        api_key=api_key
    )
    
    print(f"==== SARVAM TRANSLATION DEBUG ==== Back-translation complete")
    return back_translated_text
