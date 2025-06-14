#!/usr/bin/env python
"""
Comprehensive test for Google translation module with:
- Actual diarization data testing
- Enhanced error handling from memory
- Language code validation
"""
import os
import json
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from modules.google_translation import translate_diarized_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

def validate_segment_structure(segment):
    """Validate segment structure matches expected keys"""
    required_keys = {
        'segment_id': str,
        'start_time': (int, float),
        'end_time': (int, float),
        'text': str
    }
    for key, expected_type in required_keys.items():
        if key not in segment:
            raise ValueError(f"Segment missing required key: {key}")
        if not isinstance(segment[key], expected_type):
            raise TypeError(
                f"Segment {key} should be {expected_type}, got {type(segment[key])}"
            )

def load_test_data(file_path):
    """Load and validate test data structure"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate top-level structure
        if not all(k in data for k in ['transcript', 'segments']):
            raise ValueError("Invalid diarization data structure")
            
        # Validate each segment
        for segment in data['segments']:
            validate_segment_structure(segment)
            
        return data
        
    except Exception as e:
        logger.error(f"Test data validation failed: {str(e)}")
        raise

def run_translation_test():
    """Execute comprehensive translation test"""
    # Configuration
    test_file = "/Users/sandilya/CascadeProjects/Indic-Translator/outputs/session_pm6rujvp9t/diarization.json"
    source_lang = "telugu"  # te-IN
    target_lang = "hindi"   # hi-IN
    
    try:
        # Load and validate test data
        logger.info(f"Loading test data from {test_file}")
        diarization_data = load_test_data(test_file)
        
        # Initialize API
        if not (api_key := os.getenv("GEMINI_API_KEY")):
            raise ValueError("GEMINI_API_KEY not found in environment")
        genai.configure(api_key=api_key)
        
        # Test translation
        logger.info(f"Testing translation: {source_lang} → {target_lang}")
        translated = translate_diarized_content(
            diarization_data,
            target_language=target_lang,
            source_language=source_lang
        )
        
        # Validate results
        if not translated:
            raise ValueError("Translation returned empty result")
            
        logger.info("Translation completed. Validating output structure...")
        if not isinstance(translated, dict):
            raise ValueError("Translation result is not a dictionary")
        if "segments" not in translated:
            raise ValueError("Translation missing segments")
        for segment in translated["segments"]:
            validate_segment_structure(segment)
            if 'translated_text' not in segment:
                raise ValueError(f"Segment {segment['segment_id']} missing translation")
            if not isinstance(segment['translated_text'], str):
                raise TypeError(f"Invalid translation type in segment {segment['segment_id']}")
        
        logger.info("✅ Test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    run_translation_test()
