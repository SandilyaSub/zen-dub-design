#!/usr/bin/env python
"""
Test script for Google Gemini API to understand the correct usage pattern.
"""
import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables and API key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    exit(1)

# Configure Google Generative AI
genai.configure(api_key=GEMINI_API_KEY)

# Default safety settings
DEFAULT_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]

def load_diarization_data():
    """Load diarization data from temp/diarization.json"""
    try:
        with open('temp/diarization.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading diarization data: {e}")
        return None

def extract_json_from_response(response_text):
    """Extract JSON from response text that might be wrapped in markdown code blocks"""
    if "```json" in response_text:
        return response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        return response_text.split("```")[1].split("```")[0].strip()
    return response_text.strip()

def save_json_to_file(data, filename):
    """Save JSON data to a file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully saved JSON to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {filename}: {e}")
        return False

def translate_diarization_hindi_to_telugu():
    """Translate diarization data from Hindi to Telugu and save to file"""
    logger.info("Translating diarization data from Hindi to Telugu...")
    
    # Load diarization data
    diarization_data = load_diarization_data()
    if not diarization_data:
        logger.error("Could not load diarization data")
        return
    
    # Create model with corrected max_output_tokens
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 2048,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",
        generation_config=generation_config,
        safety_settings=DEFAULT_SAFETY_SETTINGS
    )
    
    # System prompt specifically for Hindi to Telugu translation
    system_prompt = """You are a world-class multilingual translator. Your task is to translate diarized content from Hindi to Telugu.

IMPORTANT INSTRUCTIONS:
1. The input is in Hindi language
2. You MUST translate ALL text to Telugu language (not English)
3. Preserve any English words or names that appear in the original text
4. Maintain the same JSON structure in your response

You must respond with valid JSON in the following format:
{
  "transcript": "Full translated text in Hindi",
  "segments": [
    {"text": "First segment translated to Hindi"},
    {"text": "Second segment translated to Hindi"}
  ]
}

DO NOT keep any Telugu text in your response. TRANSLATE EVERYTHING TO HINDI.
"""
    
    try:
        # Using chat with history (this method worked well in our tests)
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
            
            # Save the translated JSON to file
            output_file = 'temp/diarization_translated.json'
            save_json_to_file(json_response, output_file)
            
            # Also save the raw response for inspection
            raw_output_file = 'temp/raw_translation_response.txt'
            with open(raw_output_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Raw response saved to {raw_output_file}")
            
            return json_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response as JSON: {e}")
            # Save the raw response for debugging
            with open('temp/failed_response.txt', 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info("Raw response saved to temp/failed_response.txt")
            return None
        
    except Exception as e:
        logger.error(f"Error in diarization translation: {e}")
        return None

if __name__ == "__main__":
    logger.info("Starting Hindi to Telugu translation test")
    result = translate_diarization_hindi_to_telugu()
    if result:
        logger.info("Translation completed successfully!")
        
        # Print a few translated segments for manual validation
        logger.info("\nSample of translated segments for validation:")
        for i, segment in enumerate(result.get('segments', [])[:5]):  # Show first 5 segments
            logger.info(f"Segment {i+1}: {segment.get('text', '')}")
        
        logger.info("\nTranslation saved to temp/diarization_translated.json")
        logger.info("Please check this file to validate the translation quality.")
    else:
        logger.error("Translation failed.")
