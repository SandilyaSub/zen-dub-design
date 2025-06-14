"""
Google Translation module using Gemini API for diarized translation.
"""
import os
import json
import logging
import datetime
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv
import copy

# Set up Google Generative AI
import google.generativeai as genai

# Configure logging
import logging.handlers
import datetime


# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Get current date for log filename
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = f"logs/google_translation_{current_date}.log"

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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
logger.info(f"GEMINI_API_KEY found: {'Yes' if GEMINI_API_KEY else 'No'}")

# Configure Google Generative AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Google Generative AI configured with API key")
else:
    logger.error("No Gemini API key found in environment variables")

# Default safety settings
DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

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

def translate_with_validation(model, input_json: Dict, system_prompt: str, max_retries: int = 2) -> Dict:
    """
    Translate with validation and retry logic
    
    Args:
        model: The generative model to use
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
            
            # Send request to model
            logger.info(f"Sending translation request to Google Gemini API (attempt {attempts+1}/{max_retries+1})")
            
            # Method: Using chat with system prompt as first message
            chat_session = model.start_chat(history=[])
            # First message is the system prompt
            chat_session.send_message(current_prompt)
            # Second message is the data
            input_text = json.dumps(input_json, ensure_ascii=False)
            response = chat_session.send_message(input_text)
            
            # Log raw response for debugging
            logger.info(f"Received response from Google Gemini API: {response.text[:100]}...")
            
            # Extract JSON from response if it's wrapped in markdown code blocks
            json_text = extract_json_from_response(response.text)
            
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
            logger.warning(f"Attempt {attempts}/{max_retries+1} failed with exception: {e}")
    
    # If we get here, all attempts failed
    raise ValueError(f"Failed to get valid response after {max_retries+1} attempts. Last error: {last_error}")

def translate_diarized_content(diarization_data, target_language: str, source_language: str = "auto"):
    """
    Translate diarized content using Google Gemini.
    
    Args:
        diarization_data: Either a dictionary containing segments to translate or a list of texts
        target_language: Target language for translation
        source_language: Source language (default: auto-detect)
        
    Returns:
        If input is a dictionary: Translated diarization data
        If input is a list: List of translated texts
        
    Raises:
        ValueError: If translation fails after retries
    """
    # Check for API key
    if not GEMINI_API_KEY:
        logger.error("No Gemini API key found.")
        raise ValueError("No Gemini API key available for translation.")
    
    # Create the model with improved configuration
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,  # Reduced from 8192 to avoid API limits
    }
    
    # Handle the case where diarization_data is a list of texts
    if isinstance(diarization_data, list):
        logger.info(f"Translating list of {len(diarization_data)} text segments from {source_language} to {target_language}")
        translated_texts = []
        
        try:
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash-8b",
                generation_config=generation_config,
                safety_settings=DEFAULT_SAFETY_SETTINGS
            )
            
            # Translate each text segment
            for i, text in enumerate(diarization_data):
                if not text or text.strip() == "":
                    translated_texts.append("")
                    continue
                    
                # Simple prompt for translating a single text segment
                prompt = f"""Translate the following text from {source_language} to {target_language}:

Text: {text}

Translated text:"""
                
                try:
                    response = model.generate_content(prompt)
                    translated_text = response.text.strip()
                    translated_texts.append(translated_text)
                    logger.info(f"Translated segment {i+1}/{len(diarization_data)}")
                except Exception as e:
                    logger.error(f"Error translating segment {i}: {e}")
                    # If translation fails, keep the original text
                    translated_texts.append(text)
            
            return translated_texts
            
        except Exception as e:
            logger.error(f"Error translating text list: {e}")
            raise ValueError(f"Translation failed: {str(e)}")
    
    # For dictionary input, use the more effective approach from test_gemini_api.py
    logger.info(f"Translating diarized content from {source_language} to {target_language}")
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-8b",
            generation_config=generation_config,
            safety_settings=DEFAULT_SAFETY_SETTINGS
        )
        
        # Improved system prompt with explicit language instructions
        # Using the more effective format from test_gemini_api.py
        system_prompt = f"""You are a world-class multilingual translator. Your task is to translate diarized content from {source_language} to {target_language}.

IMPORTANT INSTRUCTIONS:
1. The input is in {source_language} language
2. You MUST translate ALL text to {target_language} language (not English)
3. Preserve any English words or names that appear in the original text
4. Maintain the same JSON structure in your response
5. KEEP the original text in the 'text' field
6. ADD the translated text in a new 'translated_text' field

You must respond with valid JSON in the following format:
{{
  "transcript": "Full translated text in {target_language}",
  "segments": [
    {{
      "text": "Original text in {source_language}",
      "translated_text": "First segment translated to {target_language}",
      ... (keep all other fields from the original segment)
    }},
    {{
      "text": "Original text in {source_language}",
      "translated_text": "Second segment translated to {target_language}",
      ... (keep all other fields from the original segment)
    }}
  ]
}}

DO NOT modify the original text in the 'text' field. Put translations ONLY in the 'translated_text' field.
"""
        
        # Check if the content is too large (more than 30 segments)
        if isinstance(diarization_data, dict) and len(diarization_data.get("segments", [])) > 30:
            logger.info(f"Large content detected with {len(diarization_data['segments'])} segments. Using chunked translation.")
            return translate_large_diarized_content(model, diarization_data, system_prompt, target_language, source_language)
        
        # For smaller content, use the direct chat approach from test_gemini_api.py
        logger.info("Using chat with system prompt as first message")
        chat = model.start_chat(history=[])
        
        # First message is the system prompt
        chat.send_message(system_prompt)
        
        # Second message is the data
        input_text = json.dumps(diarization_data, ensure_ascii=False)
        response = chat.send_message(input_text)
        
        # Extract JSON from response
        json_text = extract_json_from_response(response.text)
        
        # Try to parse the response as JSON
        try:
            json_response = json.loads(json_text)
            logger.info("Successfully parsed response as JSON")
            logger.info(f"Transcript preview: {json_response.get('transcript', '')[:100]}...")
            logger.info(f"Number of segments: {len(json_response.get('segments', []))}")
            
            # Save the raw response for debugging if needed
            debug_path = f"/tmp/raw_translation_response_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(debug_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Raw response saved to {debug_path}")
            
            return json_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {e}")
            # Save the raw response for debugging
            with open('/tmp/failed_translation_response.txt', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("Raw response saved to /tmp/failed_translation_response.txt")
            raise ValueError(f"Translation failed: Could not parse response as JSON: {e}")
        
    except Exception as e:
        logger.error(f"Error in diarization translation: {e}")
        raise ValueError(f"Translation failed: {str(e)}")

def translate_large_diarized_content(model, diarization_data: Dict, system_prompt: str, 
                                    target_language: str, source_language: str = "auto"):
    """
    Translate large diarized content by breaking it into chunks.
    
    Args:
        model: The generative model to use
        diarization_data: Diarization data containing segments to translate
        system_prompt: The system prompt for translation
        target_language: Target language for translation
        source_language: Source language (default: auto-detect)
        
    Returns:
        Translated diarization data
        
    Raises:
        ValueError: If translation fails after retries
    """
    logger.info("Breaking large content into chunks for translation")
    
    # Get segments from diarization data
    segments = diarization_data.get("segments", [])
    chunk_size = 10  # Process 10 segments at a time
    
    # Calculate number of chunks
    num_chunks = (len(segments) + chunk_size - 1) // chunk_size
    logger.info(f"Processing {len(segments)} segments in {num_chunks} chunks")
    
    # Initialize result structure
    result = {
        "transcript": "",
        "segments": []
    }
    
    # Process each chunk
    for i in range(num_chunks):
        start_idx = i * chunk_size
        end_idx = min((i + 1) * chunk_size, len(segments))
        
        logger.info(f"Processing chunk {i+1}/{num_chunks} (segments {start_idx+1}-{end_idx})")
        
        # Create chunk data with the same structure as the original
        chunk_data = {
            "transcript": " ".join([s.get("text", "") for s in segments[start_idx:end_idx]]),
            "segments": segments[start_idx:end_idx]
        }
        
        try:
            # Use the direct chat approach for each chunk
            logger.info("Using chat with system prompt as first message for chunk")
            chat = model.start_chat(history=[])
            
            # First message is the system prompt
            chat.send_message(system_prompt)
            
            # Second message is the chunk data
            input_text = json.dumps(chunk_data, ensure_ascii=False)
            response = chat.send_message(input_text)
            
            # Extract JSON from response
            json_text = extract_json_from_response(response.text)
            
            # Parse the response
            translated_chunk = json.loads(json_text)
            
            # Process translated chunk
            if translated_chunk:
                # Extract translated segments
                translated_segments = translated_chunk.get("segments", [])
                
                # Ensure we have the right number of segments
                if len(translated_segments) != len(chunk_data["segments"]):
                    logger.warning(f"Mismatch in segment count: got {len(translated_segments)}, expected {len(chunk_data['segments'])}")
                    # Try to align segments by using original segments and adding translations
                    aligned_segments = []
                    for j, orig_segment in enumerate(chunk_data["segments"]):
                        if j < len(translated_segments):
                            # Create a new segment with original data plus translation
                            new_segment = copy.deepcopy(orig_segment)
                            new_segment["translated_text"] = translated_segments[j].get("translated_text", "")
                            aligned_segments.append(new_segment)
                        else:
                            # If we don't have a translation, use the original segment with empty translation
                            orig_segment["translated_text"] = ""
                            aligned_segments.append(orig_segment)
                    translated_segments = aligned_segments
                
                # Add translated segments to result
                result["segments"].extend(translated_segments)
                
                # Append to full transcript
                if translated_chunk.get("transcript"):
                    if result["transcript"]:
                        result["transcript"] += " " + translated_chunk["transcript"]
                    else:
                        result["transcript"] = translated_chunk["transcript"]
            else:
                # If translation failed, add original segments with empty translations
                for segment in chunk_data["segments"]:
                    segment_copy = copy.deepcopy(segment)
                    segment_copy["translated_text"] = ""
                    result["segments"].append(segment_copy)
                
                logger.warning(f"Failed to translate chunk {i+1}/{num_chunks}")
        
        except Exception as e:
            logger.error(f"Error translating chunk {i+1}: {e}")
            # If a chunk fails, keep the original segments
            for s in segments[start_idx:end_idx]:
                result["segments"].append({"text": s.get("text", "")})
    
    # If we couldn't get any translations, raise an error
    if not result["segments"]:
        raise ValueError("Failed to translate any segments")
    
    # Ensure all segments have the translated_text field
    for segment in result["segments"]:
        if "translated_text" not in segment:
            segment["translated_text"] = ""
    
    return result

def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """
    Translate text using Google Gemini.
    
    Args:
        text: Text to translate
        target_lang: Target language
        source_lang: Source language (default: auto-detect)
        
    Returns:
        Translated text
    """
    # Check for API key
    if not GEMINI_API_KEY:
        logger.error("No Gemini API key found.")
        raise ValueError("No Gemini API key available for translation.")
    
    # Create the model with improved configuration
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,  # Reduced from 8192 to avoid API limits
    }
    
    # Create model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",
        generation_config=generation_config,
        safety_settings=DEFAULT_SAFETY_SETTINGS
    )
    
    # Improved system prompt
    system_prompt = f"""You are a world-class translator. Translate the following text from {source_lang} to {target_lang}.
    
IMPORTANT:
1. Preserve proper nouns, technical terms, and English words that should not be translated
2. Maintain the original formatting, including line breaks and punctuation
3. Ensure the translation is natural and fluent in {target_lang}

Respond ONLY with the translated text, without any explanations or additional commentary.
"""
    
    try:
        logger.info(f"Translating text from {source_lang} to {target_lang}")
        
        # Using chat with system prompt as first message
        chat = model.start_chat(history=[])
        # First message is the system prompt
        chat.send_message(system_prompt)
        # Second message is the text to translate
        response = chat.send_message(text)
        
        # Get the translated text
        translated_text = response.text.strip()
        
        return translated_text
        
    except Exception as e:
        logger.error(f"Error translating text: {e}")
        raise ValueError(f"Translation failed: {str(e)}")

# Language code mapping (same as in sarvam_translation.py)
LANGUAGE_MAP = {
    'hindi': 'hi-IN',
    'english': 'en-IN',
    'tamil': 'ta-IN',
    'telugu': 'te-IN',
    'kannada': 'kn-IN',
    'malayalam': 'ml-IN',
    'bengali': 'bn-IN',
    'marathi': 'mr-IN',
    'gujarati': 'gu-IN',
    'punjabi': 'pa-IN',
    'odia': 'or-IN',
    'urdu': 'ur-IN',
}
