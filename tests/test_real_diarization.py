#!/usr/bin/env python3
"""
Test script for the time-aligned TTS functionality using real diarization data.
This script uses an existing diarization file from the system to test the time-aligned TTS.
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import time-aligned TTS module
from modules.tts_time_aligner import time_aligned_tts

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_diarization_data(diarization_file):
    """Load diarization data from a file."""
    try:
        with open(diarization_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if the file has segments
        if "segments" not in data or not data["segments"]:
            logger.warning(f"No segments found in {diarization_file}")
            
            # If there are no segments but there is a transcript, create a single segment
            if "transcript" in data and data["transcript"]:
                data["segments"] = [{
                    "segment_id": "seg_001",
                    "speaker": "speaker_1",
                    "start_time": 0.0,
                    "end_time": 10.0,  # Assume 10 seconds for the single segment
                    "text": data["transcript"]
                }]
                logger.info("Created a single segment from transcript")
            else:
                logger.error("No transcript found in diarization data")
                return None
        
        return data
    except Exception as e:
        logger.error(f"Error loading diarization data: {e}")
        return None

def prepare_translation_data(diarization_data, target_language):
    """
    Prepare diarization data with translations.
    For testing purposes, we'll use the existing text as the translation.
    In a real scenario, this would be the actual translated text.
    """
    # Make a copy of the diarization data
    translation_data = diarization_data.copy()
    
    # For testing, we'll use the existing text as the translation
    # In a real scenario, this would be the actual translated text from the translation file
    
    # Check if the diarization data already has translations
    has_translations = any("translated_text" in segment for segment in translation_data.get("segments", []))
    
    if not has_translations:
        logger.info("Adding mock translations to segments for testing")
        for segment in translation_data.get("segments", []):
            # Use the original text as the translation for testing
            segment["text"] = segment.get("text", "")
    
    return translation_data

def test_time_aligned_tts(diarization_file, target_language, provider, voice_id=None):
    """Test time-aligned TTS with real diarization data."""
    
    # Load diarization data
    diarization_data = load_diarization_data(diarization_file)
    if not diarization_data:
        logger.error("Failed to load diarization data")
        return False, None
    
    # Prepare translation data
    translation_data = prepare_translation_data(diarization_data, target_language)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Output file path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = "mp3" if provider == "cartesia" else "wav"
    output_path = os.path.join(output_dir, f"{provider}_time_aligned_{timestamp}.{file_ext}")
    
    # Options for TTS
    options = {
        "bit_rate": 128000,
        "sample_rate": 44100
    }
    
    # Generate time-aligned TTS
    logger.info(f"Testing {provider} time-aligned TTS with {target_language}...")
    success = time_aligned_tts(
        diarization_data=translation_data,
        output_path=output_path,
        language=target_language,
        provider=provider,
        voice_id=voice_id,
        options=options
    )
    
    if success:
        logger.info(f"Successfully generated {provider} time-aligned TTS: {output_path}")
    else:
        logger.error(f"Failed to generate {provider} time-aligned TTS")
    
    return success, output_path

def main():
    parser = argparse.ArgumentParser(description='Test time-aligned TTS with real diarization data')
    parser.add_argument('--diarization', default='/Users/sandilya/CascadeProjects/Indic-Translator/outputs/session_a96fcpex54/diarization.json', 
                        help='Path to diarization JSON file')
    parser.add_argument('--language', default='english', help='Target language (e.g., hindi, english, telugu)')
    parser.add_argument('--provider', default='sarvam', choices=['sarvam', 'cartesia'], help='TTS provider to use')
    parser.add_argument('--voice', help='Voice ID to use')
    
    args = parser.parse_args()
    
    # Check if diarization file exists
    if not os.path.exists(args.diarization):
        logger.error(f"Diarization file not found: {args.diarization}")
        return 1
    
    # Test time-aligned TTS
    success, output_path = test_time_aligned_tts(
        diarization_file=args.diarization,
        target_language=args.language,
        provider=args.provider,
        voice_id=args.voice
    )
    
    # Print summary
    logger.info("\n--- Test Summary ---")
    logger.info(f"{args.provider.capitalize()} TTS: {'Success' if success else 'Failed'}")
    if success:
        logger.info(f"Output: {output_path}")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
