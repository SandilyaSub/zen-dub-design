"""
Claude Translation module using Anthropic's Claude API via Google Vertex AI for diarized translation.
"""
import os
import json
import logging
import datetime
import copy
from typing import Dict, List, Any, Tuple, Optional
from dotenv import load_dotenv

# Set up Anthropic Vertex API
from anthropic import AnthropicVertex

# Configure logging
import logging.handlers
import datetime

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Get current date for log filename
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
log_file = f"logs/claude_translation_{current_date}.log"

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

# Get API configuration from environment
VERTEX_REGION = os.getenv("VERTEX_REGION", "us-east5")
VERTEX_PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
logger.info(f"VERTEX_PROJECT_ID found: {'Yes' if VERTEX_PROJECT_ID else 'No'}")
logger.info(f"VERTEX_REGION set to: {VERTEX_REGION}")

# Language code mapping (same as in sarvam_translation.py)
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
    Translate with validation and retry logic using Claude via Vertex AI
    
    Args:
        client: The Claude Vertex API client
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
            
            # Send request to Claude via Vertex
            logger.info(f"Sending translation request to Claude via Vertex AI (attempt {attempts+1}/{max_retries+1})")
            
            # Prepare input data
            input_text = json.dumps(input_json, ensure_ascii=False)
            
            # Call Claude via Vertex AI
            response = client.messages.create(
                model="claude-3-7-sonnet@20250219",
                max_tokens=4000,
                temperature=0.2,  # Lower temperature for more consistent translations
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": current_prompt},
                            {"type": "text", "text": input_text}
                        ]
                    }
                ]
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Log raw response for debugging
            logger.info(f"Received response from Claude via Vertex AI: {response_text[:100]}...")
            
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

def translate_text(text: str, source_lang: str, target_lang: str, mode: str = "modern-colloquial", project_id: str = None, region: str = None) -> str:
    """
    Translate text using Claude via Vertex AI.
    
    Args:
        text: Text to translate
        source_lang: Source language
        target_lang: Target language
        mode: Translation mode ("modern-colloquial", "formal", etc.)
        project_id: Google Cloud Project ID (optional, falls back to env var)
        region: Google Cloud region (optional, falls back to env var)
        
    Returns:
        Translated text
    """
    # Get project ID and region
    vertex_project_id = project_id or VERTEX_PROJECT_ID
    vertex_region = region or VERTEX_REGION
    
    if not vertex_project_id:
        error_msg = "No Google Cloud Project ID provided or found in environment variables"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    
    # Create client
    try:
        client = AnthropicVertex(
            project_id=vertex_project_id,
            region=vertex_region
        )
    except Exception as e:
        error_msg = f"Failed to create Vertex AI client: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"
    
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
        prompt = f"""
        Translate the following text from {source_lang} to {target_lang}.
        
        Style: {mode}
        
        If the style is "modern-colloquial", preserve all English words, technical terms, and proper nouns.
        Maintain the original tone and intent of the message.
        
        Text to translate:
        {text}
        
        Translation:
        """
        
        # Call Claude via Vertex AI
        logger.info("Sending translation request to Claude via Vertex AI")
        response = client.messages.create(
            model="claude-3-7-sonnet@20250219",
            max_tokens=4000,
            temperature=0.2,  # Lower temperature for more consistent translations
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        )
        
        # Extract and clean translation
        translated_text = response.content[0].text.strip()
        
        # Log success
        logger.info(f"Translation complete: {translated_text[:30]}...")
        
        return translated_text
        
    except Exception as e:
        error_msg = f"Translation failed: {str(e)}"
        logger.error(error_msg)
        return f"Error: {error_msg}"

def claude_translate_diarized_content(diarization_data: Dict, target_language: str, source_language: str = "auto", project_id: str = None, region: str = None) -> Dict:
    """
    Translate diarized content using Claude via Vertex AI.
    
    Args:
        diarization_data: Diarization JSON data
        target_language: Target language
        source_language: Source language (default: auto)
        project_id: Google Cloud Project ID (optional, falls back to env var)
        region: Google Cloud region (optional, falls back to env var)
    
    Returns:
        Translated diarization data
    """
    # Debug info
    print(f"==== CLAUDE TRANSLATION DEBUG ==== Starting claude_translate_diarized_content for target_language={target_language}, source_language={source_language}")
    
    # Get project ID and region
    vertex_project_id = project_id or VERTEX_PROJECT_ID
    vertex_region = region or VERTEX_REGION
    
    if vertex_project_id:
        print(f"==== CLAUDE TRANSLATION DEBUG ==== VERTEX_PROJECT_ID found: {vertex_project_id}")
    else:
        error_msg = "No Google Cloud Project ID provided or found in environment variables"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Create client
    try:
        client = AnthropicVertex(
            project_id=vertex_project_id,
            region=vertex_region
        )
    except Exception as e:
        error_msg = f"Failed to create Vertex AI client: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Make a deep copy to avoid modifying the original
    result = copy.deepcopy(diarization_data)
    
    # Get segments
    segments = result.get("segments", [])
    print(f"==== CLAUDE TRANSLATION DEBUG ==== Found {len(segments)} segments to translate")
    
    # Translate each segment
    for i, segment in enumerate(segments):
        if "text" in segment and segment["text"]:
            print(f"==== CLAUDE TRANSLATION DEBUG ==== Translating segment {i+1}/{len(segments)}")
            original_text = segment["text"]
            translated_text = translate_text(
                original_text, 
                source_language, 
                target_language,
                mode="modern-colloquial",
                project_id=vertex_project_id,
                region=vertex_region
            )
            
            if translated_text.startswith("Error:"):
                print(f"==== CLAUDE TRANSLATION DEBUG ==== Error translating segment {i+1}: {translated_text}")
                continue
                
            segment["text"] = translated_text
            segment["original_text"] = original_text
            print(f"==== CLAUDE TRANSLATION DEBUG ==== Segment {i+1} translated successfully")
    
    # Add translation info
    result["translation_info"] = {
        "source_language": source_language,
        "target_language": target_language,
        "translator": "claude_ai_vertex",
        "translation_mode": "modern-colloquial"
    }
    
    print(f"==== CLAUDE TRANSLATION DEBUG ==== Translation complete for all segments")
    return result

def claude_back_translate(translated_data: Dict, original_language: str, project_id: str = None, region: str = None) -> Dict:
    """
    Back-translate content using Claude via Vertex AI.
    
    Args:
        translated_data: Translated data
        original_language: Original language to translate back to
        project_id: Google Cloud Project ID (optional, falls back to env var)
        region: Google Cloud region (optional, falls back to env var)
    
    Returns:
        Back-translated data
    """
    # Get the target language from the translation info
    target_language = translated_data.get("translation_info", {}).get("target_language")
    
    if not target_language:
        error_msg = "No target language found in translation info"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Back-translate from target language to original language
    return claude_translate_diarized_content(
        translated_data,
        original_language,
        target_language,
        project_id=project_id,
        region=region
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
    # Find current segment index
    current_index = -1
    for i, segment in enumerate(all_segments):
        if segment.get("segment_id") == current_segment.get("segment_id"):
            current_index = i
            break
    
    if current_index == -1:
        return {"previous_segments": [], "next_segments": []}
    
    # Get previous segments
    start_idx = max(0, current_index - window_size)
    previous_segments = all_segments[start_idx:current_index]
    
    # Get next segments (up to 1)
    next_segments = []
    if current_index + 1 < len(all_segments):
        next_segments = [all_segments[current_index + 1]]
    
    # Get speaker information
    current_speaker = current_segment.get("speaker", "")
    speaker_segments = [s for s in all_segments if s.get("speaker") == current_speaker]
    
    return {
        "previous_segments": previous_segments,
        "next_segments": next_segments,
        "speaker_segments": speaker_segments,
        "speaker": current_speaker
    }

def create_context_prompt(segment, context, source_lang, target_lang):
    """
    Create a context-aware prompt for Claude.
    
    Args:
        segment: The segment to translate
        context: Context information from build_segment_context
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        str: Context-enhanced system prompt
    """
    # Build context from previous segments
    previous_context = ""
    if context["previous_segments"]:
        previous_context = "Previous segments:\n"
        for prev in context["previous_segments"]:
            previous_context += f"- Speaker {prev.get('speaker', 'unknown')}: {prev.get('text', '')}\n"
    
    # Build context from next segment if available
    next_context = ""
    if context["next_segments"]:
        next_context = "Next segment:\n"
        for next_seg in context["next_segments"]:
            next_context += f"- Speaker {next_seg.get('speaker', 'unknown')}: {next_seg.get('text', '')}\n"
    
    # Create the prompt
    prompt = f"""
    You are a professional translator specializing in {source_lang} to {target_lang} translation.
    
    Translate the following segment from {source_lang} to {target_lang}.
    
    IMPORTANT GUIDELINES:
    - Preserve all English words, technical terms, and proper nouns
    - Maintain the original tone and intent
    - Use modern, colloquial language that sounds natural
    - If there are cultural references, adapt them appropriately
    
    {previous_context}
    
    SEGMENT TO TRANSLATE:
    Speaker {segment.get('speaker', 'unknown')}: {segment.get('text', '')}
    
    {next_context}
    
    Respond with ONLY the translated text, nothing else.
    """
    
    return prompt

def translate_segment_with_context(client, segment, all_segments, source_lang, target_lang, project_id=None, region=None):
    """
    Translate a single segment with enhanced context.
    
    Args:
        client: The Claude Vertex API client
        segment: The segment to translate
        all_segments: All segments in the diarization
        source_lang: Source language
        target_lang: Target language
        project_id: Google Cloud Project ID (optional)
        region: Google Cloud region (optional)
        
    Returns:
        str: Translated text
    """
    # Build context
    context = build_segment_context(segment, all_segments)
    
    # Create context-aware prompt
    prompt = create_context_prompt(segment, context, source_lang, target_lang)
    
    try:
        # Call Claude via Vertex AI
        response = client.messages.create(
            model="claude-3-7-sonnet@20250219",
            max_tokens=1000,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}]
                }
            ]
        )
        
        # Extract and clean translation
        translated_text = response.content[0].text.strip()
        
        return translated_text
        
    except Exception as e:
        logger.error(f"Context-aware translation failed: {str(e)}")
        # Fall back to regular translation
        return translate_text(
            segment.get("text", ""),
            source_lang,
            target_lang,
            project_id=project_id,
            region=region
        )

def claude_translate_diarized_content_context_aware(diarization_data, target_language, source_language="auto", project_id=None, region=None):
    """
    Translate diarized content using Claude via Vertex AI with context awareness.
    
    Args:
        diarization_data: Diarization JSON data
        target_language: Target language
        source_language: Source language (default: auto)
        project_id: Google Cloud Project ID (optional)
        region: Google Cloud region (optional)
    
    Returns:
        Translated diarization data
    """
    # Get project ID and region
    vertex_project_id = project_id or VERTEX_PROJECT_ID
    vertex_region = region or VERTEX_REGION
    
    if not vertex_project_id:
        error_msg = "No Google Cloud Project ID provided or found in environment variables"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Create client
    try:
        client = AnthropicVertex(
            project_id=vertex_project_id,
            region=vertex_region
        )
    except Exception as e:
        error_msg = f"Failed to create Vertex AI client: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Make a deep copy to avoid modifying the original
    result = copy.deepcopy(diarization_data)
    
    # Get segments
    segments = result.get("segments", [])
    logger.info(f"Found {len(segments)} segments to translate with context")
    
    # Translate each segment with context
    for i, segment in enumerate(segments):
        if "text" in segment and segment["text"]:
            logger.info(f"Translating segment {i+1}/{len(segments)} with context")
            original_text = segment["text"]
            
            translated_text = translate_segment_with_context(
                client,
                segment,
                segments,
                source_language,
                target_language,
                project_id=vertex_project_id,
                region=vertex_region
            )
            
            if translated_text.startswith("Error:"):
                logger.error(f"Error translating segment {i+1} with context: {translated_text}")
                continue
                
            segment["text"] = translated_text
            segment["original_text"] = original_text
            logger.info(f"Segment {i+1} translated successfully with context")
    
    # Add translation info
    result["translation_info"] = {
        "source_language": source_language,
        "target_language": target_language,
        "translator": "claude_ai_vertex",
        "translation_mode": "modern-colloquial-context-aware"
    }
    
    logger.info("Context-aware translation complete for all segments")
    return result
