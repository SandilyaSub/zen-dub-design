"""
Google Translation module using Gemini API for diarized translation.
"""
import os
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

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
    
    # Original implementation for dictionary input
    # Improved system prompt with explicit language instructions
    system_prompt = f"""You are a world-class multilingual translator. Your task is to translate diarized content from {source_language} to {target_language}.

CRITICAL INSTRUCTIONS:
1. Ensure that the meaning of the message and the context is preserved in the translation
2. You will be shared a JSON object containing the diarized content
3. The text that you need to translate is in the key "text" of each segment
4. The input is in {source_language} language
5. You MUST translate ALL text to {target_language} language
6. Preserve any English words or names that appear in the original text
7. Maintain the same JSON structure in your response
8. EVERYTHING MUST ONLY BE IN {target_language} . DO NOT RETURN TEXT IN {source_language} OR ANY OTHER LANGUAGE.


You must respond with valid JSON in the following format:
{{
  "transcript": "Full translated text in {target_language}",
  "segments": [
    {{"text": "First segment translated to {target_language}"}},
    {{"text": "Second segment translated to {target_language}"}}
  ]
}}

IMPORTANT: TRANSLATE EVERYTHING TO {target_language}. DO NOT KEEP ANY TEXT IN THE ORIGINAL LANGUAGE.
"""
    
    logger.info(f"Translating diarized content from {source_language} to {target_language}")
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-8b",
            generation_config=generation_config,
            safety_settings=DEFAULT_SAFETY_SETTINGS
        )
        
        # Check if the content is too large (more than 10 segments)
        if len(diarization_data.get("segments", [])) > 10:
            logger.info(f"Large content detected with {len(diarization_data['segments'])} segments. Using chunked translation.")
            return translate_large_diarized_content(model, diarization_data, system_prompt, target_language, source_language)
        
        # For smaller content, use the standard approach
        return translate_with_validation(model, diarization_data, system_prompt)
        
    except Exception as e:
        logger.error(f"Error translating diarized content: {e}")
        raise ValueError(f"Translation failed: {str(e)}")

def translate_large_diarized_content(model, diarization_data: Dict, system_prompt: str, 
                                    target_language: str, source_language: str = "auto") -> Dict:
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
    
    # Extract segments from the original data
    segments = diarization_data.get("segments", [])
    total_segments = len(segments)
    
    # Create chunks of 10 segments each
    chunk_size = 10
    chunks = [segments[i:i + chunk_size] for i in range(0, total_segments, chunk_size)]
    logger.info(f"Created {len(chunks)} chunks from {total_segments} segments")
    
    # Translate each chunk
    translated_segments = []
    chunk_transcripts = []
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Translating chunk {i+1}/{len(chunks)} with {len(chunk)} segments")
        
        # Create a smaller diarization data structure for this chunk
        chunk_data = {
            "transcript": " ".join([segment.get("text", "") for segment in chunk]),
            "segments": chunk
        }
        
        # Add chunk-specific instructions to the system prompt
        chunk_prompt = system_prompt + f"\n\nThis is chunk {i+1} of {len(chunks)}. Focus only on translating the segments provided."
        
        try:
            # Translate this chunk
            translated_chunk = translate_with_validation(model, chunk_data, chunk_prompt)
            
            # Extract the translated segments and add them to our result
            translated_segments.extend(translated_chunk.get("segments", []))
            chunk_transcripts.append(translated_chunk.get("transcript", ""))
            
            logger.info(f"Successfully translated chunk {i+1}/{len(chunks)}")
            
        except Exception as e:
            logger.error(f"Error translating chunk {i}: {e}")
            # If a chunk fails, create placeholder segments to maintain structure
            for segment in chunk:
                translated_segments.append({
                    "speaker": segment.get("speaker", ""),
                    "text": f"[Translation error: {str(e)}]",
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0)
                })
    
    # Combine all translated chunks into a single result
    result = {
        "transcript": " ".join(chunk_transcripts),
        "segments": translated_segments
    }
    
    # Ensure we preserve all metadata from the original segments
    for i, segment in enumerate(result["segments"]):
        if i < total_segments:
            # Copy all metadata except 'text' from the original segment
            for key, value in segments[i].items():
                if key != "text":
                    segment[key] = value
    
    logger.info(f"Completed translation of all {len(chunks)} chunks")
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
