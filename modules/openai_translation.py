"""
OpenAI Translation module using GPT-4.1 API for diarized translation.
"""
import os
import json
import logging
import datetime
import copy
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Set up OpenAI
from openai import OpenAI

# Configure logging
import logging.handlers
import datetime

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Get current date for log filename
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = f"logs/openai_translation_{current_date}.log"

# Configure logging to both console and file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler
file_handler = logging.handlers.RotatingFileHandler(
    log_file, maxBytes=10485760, backupCount=5, encoding="utf-8"
)
file_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
logger.info(f"OPENAI_API_KEY found: {'Yes' if OPENAI_API_KEY else 'No'}")

# Default model
DEFAULT_MODEL = "gpt-4.1-2025-04-14"

# Language code mapping
LANGUAGE_MAP = {
    'hindi': 'hi-IN',
    'english': 'en-IN',
    'bengali': 'bn-IN',
    'gujarati': 'gu-IN',
    'kannada': 'kn-IN',
    'malayalam': 'ml-IN',
    'marathi': 'mr-IN',
    'punjabi': 'pa-IN',
    'tamil': 'ta-IN',
    'telugu': 'te-IN',
    'urdu': 'ur-IN',
    'nepali': 'ne-NP',
    'sinhala': 'si-LK',
}

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

def translate_with_validation(client, input_json: Dict, system_prompt: str, max_retries: int = 2) -> Dict:
    """
    Translate with validation and retry logic using OpenAI
    
    Args:
        client: The OpenAI client
        input_json: The input JSON to translate
        system_prompt: The system prompt for translation
        max_retries: Maximum number of retries (default: 2)
        
    Returns:
        Translated JSON data
        
    Raises:
        ValueError: If all translation attempts fail
    """
    attempts = 0
    last_error = ""
    
    while attempts <= max_retries:
        try:
            # If this isn't the first attempt, add feedback about the previous error
            current_prompt = system_prompt
            if attempts > 0:
                feedback = f"""
                Your previous response was not in the expected format. 
                Error: {last_error}
                
                IMPORTANT: You must respond with valid JSON that includes:
                - A "transcript" field with the full translated text
                - A "segments" array containing objects with "text" fields
                
                Example format:
                {{
                  "transcript": "Full translated text here",
                  "segments": [
                    {{"text": "First segment translated"}},
                    {{"text": "Second segment translated"}}
                  ]
                }}
                """
                current_prompt = system_prompt + "\n\n" + feedback
            
            # Send request to OpenAI
            logger.info(f"Sending translation request to OpenAI (attempt {attempts+1}/{max_retries+1})")
            
            # Prepare input data
            input_text = json.dumps(input_json, ensure_ascii=False)
            
            # Call OpenAI API
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": current_prompt},
                    {"role": "user", "content": input_text}
                ],
                temperature=0.2,  # Lower temperature for more consistent translations
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            
            # Log raw response for debugging
            logger.info(f"Received response from OpenAI: {response_text[:100]}...")
            
            # Extract JSON from response if it's wrapped in markdown code blocks
            json_text = extract_json_from_response(response_text)
            
            # Validate response
            is_valid, error = is_valid_diarization_json(json_text)
            
            if is_valid:
                return json.loads(json_text)
            else:
                last_error = error
                attempts += 1
                logger.warning(f"Attempt {attempts}/{max_retries+1} failed: {error}")
                
        except Exception as e:
            last_error = str(e)
            attempts += 1
            logger.error(f"Translation attempt {attempts} failed: {str(e)}")
            
            if attempts > max_retries:
                logger.error(f"All {max_retries+1} translation attempts failed")
                raise ValueError(f"Translation failed after {max_retries+1} attempts: {last_error}")
    
    # This should not be reached due to the raise in the loop, but just in case
    raise ValueError(f"Translation failed after {max_retries+1} attempts: {last_error}")

def translate_text(text: str, source_lang: str, target_lang: str, mode: str = "modern-colloquial", api_key: str = None) -> str:
    """
    Translate text using OpenAI.
    
    Args:
        text: Text to translate
        source_lang: Source language
        target_lang: Target language
        mode: Translation mode ("modern-colloquial", "formal", etc.)
        api_key: OpenAI API key (optional, falls back to env var)
        
    Returns:
        Translated text
    """
    # Get API key
    openai_api_key = api_key or OPENAI_API_KEY
    if not openai_api_key:
        error_msg = "No OpenAI API key provided or found in environment variables"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    
    # Create client
    client = OpenAI(api_key=openai_api_key)
    
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
    
    logger.info(f"Translating from {source_lang} to {target_lang}")
    
    try:
        # Craft prompt with clear instructions
        system_prompt = f"""You are a world-class translator. Translate the following text from {source_lang} to {target_lang}.
        
IMPORTANT:
1. Preserve proper nouns, technical terms, and English words that should not be translated
2. Maintain the original formatting, including line breaks and punctuation
3. Ensure the translation is natural and fluent in {target_lang}
4. Style: {mode}

If the style is "modern-colloquial", preserve all English words, technical terms, and proper nouns.

Respond ONLY with the translated text, without any explanations or additional commentary.
"""
        
        # Call OpenAI API
        logger.info("Sending translation request to OpenAI")
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.2,  # Lower temperature for more consistent translations
        )
        
        # Extract and clean translation
        translated_text = response.choices[0].message.content.strip()
        
        # Log success
        logger.info(f"Translation complete: {translated_text[:30]}...")
        
        return translated_text
        
    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

def openai_translate_diarized_content(diarization_data: Dict, target_language: str, source_language: str = "auto", api_key: str = None) -> Dict:
    """
    Translate diarized content using OpenAI.
    
    Args:
        diarization_data: Diarization JSON data
        target_language: Target language
        source_language: Source language (default: auto)
        api_key: OpenAI API key (optional)
    
    Returns:
        Translated diarization data
    """
    # Debug info
    print(f"==== OPENAI TRANSLATION DEBUG ==== Starting openai_translate_diarized_content for target_language={target_language}, source_language={source_language}")
    
    # Get API key
    openai_api_key = api_key or OPENAI_API_KEY
    if openai_api_key:
        print(f"==== OPENAI TRANSLATION DEBUG ==== OPENAI_API_KEY found with length: {len(openai_api_key)}")
    else:
        error_msg = "No OpenAI API key provided or found in environment variables"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Create client
    client = OpenAI(api_key=openai_api_key)
    
    # Make a deep copy to avoid modifying the original
    result = copy.deepcopy(diarization_data)
    
    # Get segments
    segments = result.get("segments", [])
    print(f"==== OPENAI TRANSLATION DEBUG ==== Found {len(segments)} segments to translate")
    
    # Translate each segment
    for i, segment in enumerate(segments):
        if "text" in segment and segment["text"]:
            print(f"==== OPENAI TRANSLATION DEBUG ==== Translating segment {i+1}/{len(segments)}")
            original_text = segment["text"]
            translated_text = translate_text(
                original_text, 
                source_language, 
                target_language,
                mode="modern-colloquial",
                api_key=openai_api_key
            )
            
            if translated_text.startswith("Error:"):
                print(f"==== OPENAI TRANSLATION DEBUG ==== Error translating segment {i+1}: {translated_text}")
                continue
                
            segment["text"] = translated_text
            segment["original_text"] = original_text
            print(f"==== OPENAI TRANSLATION DEBUG ==== Segment {i+1} translated successfully")
    
    # Add translation info
    result["translation_info"] = {
        "source_language": source_language,
        "target_language": target_language,
        "translator": "openai_gpt4.1",
        "translation_mode": "modern-colloquial"
    }
    
    print(f"==== OPENAI TRANSLATION DEBUG ==== Translation complete for all segments")
    return result

def openai_back_translate(translated_data: Dict, original_language: str, api_key: str = None) -> Dict:
    """
    Back-translate content using OpenAI.
    
    Args:
        translated_data: Translated data
        original_language: Original language
        api_key: OpenAI API key (optional)
    
    Returns:
        Back-translated data
    """
    # Extract target language from translation_info
    target_language = translated_data.get("translation_info", {}).get("source_language", "auto")
    
    # Call translate_diarized_content with reversed language parameters
    return openai_translate_diarized_content(
        translated_data,
        original_language,
        target_language,
        api_key=api_key
    )

def build_segment_context(current_segment, all_segments, window_size=3):
    """
    Create rich context for translation.
    
    Args:
        current_segment: The segment being translated
        all_segments: All segments in the diarization
        window_size: Number of previous segments to include
        
    Returns:
        dict: Context information for translation
    """
    # Get segment index
    segment_idx = -1
    for i, segment in enumerate(all_segments):
        if segment.get("segment_id") == current_segment.get("segment_id"):
            segment_idx = i
            break
    
    if segment_idx == -1:
        # Segment not found, return minimal context
        return {
            "speaker": current_segment.get("speaker", "UNKNOWN"),
            "previous_segments": [],
            "current_segment": current_segment.get("text", ""),
        }
    
    # Get previous segments from the same speaker
    previous_segments = []
    speaker = current_segment.get("speaker", "UNKNOWN")
    
    # Look back up to window_size segments from the same speaker
    count = 0
    for i in range(segment_idx - 1, -1, -1):
        if count >= window_size:
            break
        
        if all_segments[i].get("speaker") == speaker:
            previous_segments.insert(0, all_segments[i].get("text", ""))
            count += 1
    
    # Return context
    return {
        "speaker": speaker,
        "previous_segments": previous_segments,
        "current_segment": current_segment.get("text", ""),
    }

def create_context_prompt(segment, context, source_lang, target_lang):
    """
    Create a context-aware prompt for OpenAI.
    
    Args:
        segment: The segment to translate
        context: Context information from build_segment_context
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        str: Context-enhanced system prompt
    """
    # Build context string
    context_str = ""
    if context["previous_segments"]:
        context_str = "Previous statements by the same speaker:\n"
        for i, prev in enumerate(context["previous_segments"]):
            context_str += f"{i+1}. {prev}\n"
    
    # Build prompt
    prompt = f"""You are a world-class translator. Translate the following text from {source_lang} to {target_lang}.

CONTEXT INFORMATION:
Speaker: {context["speaker"]}
{context_str}

TEXT TO TRANSLATE:
{context["current_segment"]}

IMPORTANT:
1. Preserve proper nouns, technical terms, and English words that should not be translated
2. Maintain the original tone and style of the speaker
3. Ensure the translation is natural and fluent in {target_lang}
4. Use the context to ensure consistent translation of terms and phrases
5. Preserve all English words, technical terms, and proper nouns

Respond ONLY with the translated text, without any explanations or additional commentary.
"""
    
    return prompt

def translate_segment_with_context(client, segment, all_segments, source_lang, target_lang, api_key=None):
    """
    Translate a single segment with enhanced context.
    
    Args:
        client: The OpenAI client
        segment: The segment to translate
        all_segments: All segments in the diarization
        source_lang: Source language
        target_lang: Target language
        api_key: OpenAI API key (optional)
        
    Returns:
        str: Translated text
    """
    # Build context
    context = build_segment_context(segment, all_segments)
    
    # Create context-aware prompt
    prompt = create_context_prompt(segment, context, source_lang, target_lang)
    
    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1000,
        )
        
        # Extract translation
        translated_text = response.choices[0].message.content.strip()
        
        return translated_text
        
    except Exception as e:
        logger.error(f"Error translating segment with context: {e}")
        # Fall back to regular translation
        return translate_text(
            segment.get("text", ""),
            source_lang,
            target_lang,
            api_key=api_key
        )

def openai_translate_diarized_content_context_aware(diarization_data, target_language, source_language="auto", api_key=None):
    """
    Translate diarized content using OpenAI with context awareness.
    
    Args:
        diarization_data: Diarization JSON data
        target_language: Target language for translation
        source_language: Source language (default: auto)
        api_key: OpenAI API key (optional)
    
    Returns:
        Translated diarization data
    """
    # Get API key
    openai_api_key = api_key or OPENAI_API_KEY
    if not openai_api_key:
        error_msg = "No OpenAI API key provided or found in environment variables"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Create client
    client = OpenAI(api_key=openai_api_key)
    
    # Make a deep copy to avoid modifying the original
    result = copy.deepcopy(diarization_data)
    
    # Get segments
    segments = result.get("segments", [])
    
    # Translate each segment with context
    for i, segment in enumerate(segments):
        if "text" in segment and segment["text"]:
            translated_text = translate_segment_with_context(
                client,
                segment,
                segments,
                source_language,
                target_language,
                api_key=openai_api_key
            )
            
            if translated_text.startswith("Error:"):
                logger.error(f"Error translating segment {i}: {translated_text}")
                continue
                
            segment["text"] = translated_text
            segment["original_text"] = segment["text"]
    
    # Add translation info
    result["translation_info"] = {
        "source_language": source_language,
        "target_language": target_language,
        "translator": "openai_gpt4.1",
        "translation_mode": "modern-colloquial-context-aware"
    }
    
    return result
