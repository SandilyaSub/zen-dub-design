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

# Import Secret Manager utility
from utils.secret_manager import get_secret

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

# Function to get Gemini API key from Secret Manager or environment variables
def get_gemini_api_key():
    """Get the Gemini API key from Secret Manager or environment variables."""
    api_key = get_secret("gemini-api-key")
    if api_key:
        logger.info(f"API key is present with length: {len(api_key)}")
        logger.info(f"First 4 chars of API key: {api_key[:4]}")
        # Validate that it's not a placeholder value
        if api_key.startswith("your") or api_key == "placeholder" or api_key == "your-api-key-here":
            logger.error(f"Invalid Gemini API key detected: {api_key}")
            return None
    else:
        logger.error("Failed to retrieve Gemini API key")
    return api_key

# Get Gemini API key
GEMINI_API_KEY = get_gemini_api_key()
logger.info(f"GEMINI_API_KEY found: {'Yes' if GEMINI_API_KEY else 'No'}")

# Configure Gemini API
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
    # Add explicit debug logging
    print(f"==== GOOGLE TRANSLATION DEBUG ==== Starting translate_diarized_content for target_language={target_language}, source_language={source_language}")
    
    # Get API key
    api_key = get_gemini_api_key()
    if not api_key:
        error_msg = "Failed to retrieve Gemini API key"
        print(f"==== GOOGLE TRANSLATION DEBUG ==== Error: {error_msg}")
        raise ValueError(error_msg)
    
    print(f"==== GOOGLE TRANSLATION DEBUG ==== GEMINI_API_KEY found with length: {len(api_key)}")
    
    # Configure Google Generative AI
    try:
        genai.configure(api_key=api_key)
        print("==== GOOGLE TRANSLATION DEBUG ==== Successfully configured Google Generative AI")
    except Exception as e:
        error_msg = f"Error configuring Google Generative AI: {str(e)}"
        print(f"==== GOOGLE TRANSLATION DEBUG ==== {error_msg}")
        raise ValueError(error_msg)
    
    # Handle list input (simple text translation)
    if isinstance(diarization_data, list):
        print(f"==== GOOGLE TRANSLATION DEBUG ==== Translating list of {len(diarization_data)} texts")
        logger.info(f"Translating list of {len(diarization_data)} texts")
        return [translate_text(text, target_language, source_language) for text in diarization_data]
    
    # Handle dictionary input (diarization data)
    print(f"==== GOOGLE TRANSLATION DEBUG ==== Translating diarized content to {target_language}")
    logger.info(f"Translating diarized content to {target_language}")
    
    # Make a copy to avoid modifying the original
    diarization_copy = copy.deepcopy(diarization_data)
    
    # Set up generation config
    generation_config = {
        "temperature": 0.2,  # Lower temperature for more consistent translations
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    # Safety settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    try:
        print("==== GOOGLE TRANSLATION DEBUG ==== Creating GenerativeModel")
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash-preview-05-20",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        print("==== GOOGLE TRANSLATION DEBUG ==== Successfully created GenerativeModel")
        
        # Get all segments
        all_segments = diarization_copy.get("segments", [])
        if not all_segments:
            print("==== GOOGLE TRANSLATION DEBUG ==== Warning: No segments found in diarization data")
            logger.warning("No segments found in diarization data")
            return diarization_copy
        
        print(f"==== GOOGLE TRANSLATION DEBUG ==== Found {len(all_segments)} segments to translate")
        
        # Add metadata for tracking
        if "metadata" not in diarization_copy:
            diarization_copy["metadata"] = {}
            
        diarization_copy["metadata"]["translation"] = {
            "source_language": source_language,
            "target_language": target_language,
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "context-enhanced-v1"
        }
        
        # IMPROVED ERROR HANDLING: Process segments with better error handling
        translated_segments_count = 0
        for i, segment in enumerate(all_segments):
            try:
                print(f"==== GOOGLE TRANSLATION DEBUG ==== Translating segment {i+1}/{len(all_segments)}: {segment.get('segment_id', 'unknown')}")
                
                # Translate with context
                translated_text = translate_segment_with_context(
                    model, 
                    segment, 
                    all_segments,
                    source_language, 
                    target_language
                )
                
                print(f"==== GOOGLE TRANSLATION DEBUG ==== Successfully translated segment {i+1}")
                
                # Update segment with translation
                segment["translated_text"] = translated_text
                translated_segments_count += 1
                
            except Exception as e:
                error_msg = f"Error translating segment {segment.get('segment_id', 'unknown')}: {str(e)}"
                print(f"==== GOOGLE TRANSLATION DEBUG ==== {error_msg}")
                logger.error(error_msg)
                # Provide a clear error message in the translation
                segment["translated_text"] = f"[Translation error: {str(e)}]"
        
        # IMPROVED VALIDATION: Check if we successfully translated any segments
        if translated_segments_count == 0:
            error_msg = "Failed to translate any segments successfully"
            print(f"==== GOOGLE TRANSLATION DEBUG ==== {error_msg}")
            logger.error(error_msg)
            raise ValueError("Translation failed: No segments were successfully translated")
        
        print(f"==== GOOGLE TRANSLATION DEBUG ==== Successfully translated {translated_segments_count}/{len(all_segments)} segments")
        
        # Update full transcript if present
        if "transcript" in diarization_copy:
            # IMPROVED ERROR HANDLING: Use a try-except block for transcript creation
            try:
                full_text = " ".join([s.get("translated_text", "") for s in all_segments if s.get("translated_text")])
                if not full_text:
                    full_text = "[Translation failed to produce any output]"
                diarization_copy["transcript"] = full_text
                print("==== GOOGLE TRANSLATION DEBUG ==== Successfully created full transcript")
            except Exception as e:
                error_msg = f"Error creating full transcript: {str(e)}"
                print(f"==== GOOGLE TRANSLATION DEBUG ==== {error_msg}")
                logger.error(error_msg)
                diarization_copy["transcript"] = "[Error creating full transcript]"
        
        print("==== GOOGLE TRANSLATION DEBUG ==== Translation completed successfully")
        return diarization_copy
        
    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        print(f"==== GOOGLE TRANSLATION DEBUG ==== {error_msg}")
        import traceback
        print(f"==== GOOGLE TRANSLATION DEBUG ==== Traceback: {traceback.format_exc()}")
        logger.error(error_msg)
        
        # IMPROVED ERROR RECOVERY: Return a minimal valid structure instead of raising an exception
        # This helps prevent JSON parsing errors downstream
        fallback_result = {
            "transcript": f"[Translation failed: {str(e)}]",
            "segments": []
        }
        
        # Copy original segments with error messages
        for i, segment in enumerate(diarization_data.get("segments", [])):
            segment_copy = {
                "segment_id": segment.get("segment_id", f"segment_{i}"),
                "text": segment.get("text", ""),
                "translated_text": f"[Translation failed: {str(e)}]",
                "speaker": segment.get("speaker", "SPEAKER_00"),
                "start_time": segment.get("start_time", segment.get("start", 0)),
                "end_time": segment.get("end_time", segment.get("end", 0))
            }
            fallback_result["segments"].append(segment_copy)
            
        # Add metadata
        fallback_result["metadata"] = {
            "translation": {
                "source_language": source_language,
                "target_language": target_language,
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e)
            }
        }
        
        print("==== GOOGLE TRANSLATION DEBUG ==== Returning fallback result structure")
        return fallback_result

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
    # Find segment index
    segment_index = next((i for i, s in enumerate(all_segments) 
                         if s["segment_id"] == current_segment["segment_id"]), -1)
    
    if segment_index == -1:
        logger.warning(f"Segment {current_segment['segment_id']} not found in all_segments")
        return {"previous_segments": [], "speaker_history": []}
    
    # Get previous segments
    prev_segments = all_segments[max(0, segment_index-window_size):segment_index]
    
    # Get speaker history (segments from same speaker)
    speaker = current_segment.get("speaker")
    speaker_segments = []
    if speaker:
        speaker_segments = [s for s in all_segments[:segment_index] 
                           if s.get("speaker") == speaker][-3:]
    
    return {
        "previous_segments": prev_segments,
        "speaker_history": speaker_segments,
        "speaker_id": speaker,
        "segment_position": segment_index,
        "total_segments": len(all_segments)
    }

def create_context_prompt(segment, context, source_lang, target_lang):
    """
    Create a context-aware prompt for Gemini.
    
    Args:
        segment: The segment to translate
        context: Context information from build_segment_context
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        str: Context-enhanced system prompt
    """
    # Format previous context
    prev_context = ""
    if context["previous_segments"]:
        prev_texts = [f"[{s.get('speaker', 'UNKNOWN')}]: {s.get('text', '')}" 
                     for s in context["previous_segments"]]
        prev_context = "Previous conversation:\n" + "\n".join(prev_texts)
    
    # Add speaker consistency if available
    speaker_context = ""
    if context["speaker_history"]:
        speaker_texts = [s.get('text', '') for s in context["speaker_history"]]
        speaker_context = f"\nSame speaker previously said:\n" + "\n".join(speaker_texts)
    
    system_prompt = f"""You are a world-class multilingual translator. Your task is to translate from {source_lang} to {target_lang}.

CONTEXT INFORMATION:
{prev_context}
{speaker_context}

Speaker ID: {context.get("speaker_id", "UNKNOWN")}
Segment position: {context.get("segment_position", 0)+1} of {context.get("total_segments", 1)}

TRANSLATION TASK:
Translate the following text, maintaining the original meaning, tone, and context:
"{segment.get('text', '')}"

RESPONSE FORMAT:
Return ONLY the translated text without any explanation or formatting.
"""
    
    return system_prompt

def translate_segment_with_context(model, segment, all_segments, source_lang, target_lang):
    """
    Translate a single segment with enhanced context.
    
    Args:
        model: The generative model to use
        segment: The segment to translate
        all_segments: All segments in the diarization
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        str: Translated text
    """
    try:
        # Build rich context
        context = build_segment_context(segment, all_segments)
        
        # Create context-aware prompt
        prompt = create_context_prompt(segment, context, source_lang, target_lang)
        
        # Get translation from Gemini
        response = model.generate_content(prompt)
        translated_text = response.text.strip()
        
        # Simple validation
        if not translated_text:
            logger.warning(f"Empty translation received for segment {segment.get('segment_id', 'unknown')}")
            return f"[Translation error for segment {segment.get('segment_id', 'unknown')}]"
        
        return translated_text
    
    except Exception as e:
        logger.error(f"Error translating segment {segment.get('segment_id', 'unknown')}: {str(e)}")
        return f"[Translation error: {str(e)}]"

def translate_diarized_content_context_aware(diarization_data, target_language: str, source_language: str = "auto"):
    """
    Translate diarized content using Google Gemini with context awareness.
    
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
    # Get API key
    api_key = get_gemini_api_key()
    if not api_key:
        raise ValueError("Failed to retrieve Gemini API key")
    
    # Configure Google Generative AI
    genai.configure(api_key=api_key)
    
    # Handle list input (simple text translation)
    if isinstance(diarization_data, list):
        logger.info(f"Translating list of {len(diarization_data)} texts")
        return [translate_text(text, target_language, source_language) for text in diarization_data]
    
    # Handle dictionary input (diarization data)
    logger.info(f"Translating diarized content to {target_language}")
    
    # Make a copy to avoid modifying the original
    diarization_copy = copy.deepcopy(diarization_data)
    
    # Set up generation config
    generation_config = {
        "temperature": 0.2,  # Lower temperature for more consistent translations
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    
    # Safety settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-8b",
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Get all segments
        all_segments = diarization_copy.get("segments", [])
        if not all_segments:
            logger.warning("No segments found in diarization data")
            return diarization_copy
        
        # Add metadata for tracking
        if "metadata" not in diarization_copy:
            diarization_copy["metadata"] = {}
            
        diarization_copy["metadata"]["translation"] = {
            "source_language": source_language,
            "target_language": target_language,
            "timestamp": datetime.datetime.now().isoformat(),
            "version": "context-enhanced-v1"
        }
        
        # Process each segment with context
        for segment in all_segments:
            try:
                # Translate with context
                translated_text = translate_segment_with_context(
                    model, 
                    segment, 
                    all_segments,
                    source_language, 
                    target_language
                )
                
                # Update segment with translation
                segment["translated_text"] = translated_text
                
            except Exception as e:
                logger.error(f"Error translating segment {segment.get('segment_id', 'unknown')}: {str(e)}")
                segment["translated_text"] = f"[Translation error: {str(e)}]"
        
        # Update full transcript if present
        if "transcript" in diarization_copy:
            full_text = " ".join([s.get("translated_text", "") for s in all_segments])
            diarization_copy["transcript"] = full_text
            
        return diarization_copy
        
    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)
