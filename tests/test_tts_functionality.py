#!/usr/bin/env python3
"""
Test script to verify TTS functionality with the bundled FFmpeg.
This script tests both Cartesia and Sarvam TTS with our FFmpeg integration.
"""

import os
import json
import logging
import tempfile
from pathlib import Path

# Import our patched module first to ensure FFmpeg is properly configured
from modules import tts_processor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_diarization_file():
    """Create a test diarization file with sample segments."""
    test_data = {
        "segments": [
            {
                "segment_id": "segment_1",
                "start_time": 0.0,
                "end_time": 2.0,
                "speaker": "speaker_1",
                "text": "Hello, this is a test.",
                "translated_text": "नमस्ते, यह एक परीक्षण है।",
                "target_language": "hindi"
            },
            {
                "segment_id": "segment_2",
                "start_time": 3.0,
                "end_time": 5.0,
                "speaker": "speaker_2",
                "text": "This is another test segment.",
                "translated_text": "यह एक और परीक्षण खंड है।",
                "target_language": "hindi"
            }
        ]
    }
    
    # Create a temporary directory for test files
    test_dir = os.path.join(tempfile.gettempdir(), "tts_test")
    os.makedirs(test_dir, exist_ok=True)
    
    # Write the test data to a file
    test_file = os.path.join(test_dir, "diarization_translated.json")
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    return test_file, test_dir

def test_tts_functionality():
    """Test TTS functionality with the bundled FFmpeg."""
    try:
        logger.info("Creating test diarization file...")
        diarization_file, test_dir = create_test_diarization_file()
        
        logger.info(f"Test diarization file created at: {diarization_file}")
        
        # Create a TTSProcessor instance
        session_id = "test_session"
        processor = tts_processor.TTSProcessor(session_id, test_dir)
        
        # Process TTS
        logger.info("Processing TTS...")
        output_file = processor.process_tts(diarization_file)
        
        # Verify the output file exists
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            logger.info(f"Generated audio file: {output_file} ({file_size} bytes)")
            logger.info("✅ TTS functionality test PASSED")
            return True
        else:
            logger.error(f"❌ TTS functionality test FAILED: Output file not found: {output_file}")
            return False
            
    except Exception as e:
        logger.error(f"❌ TTS functionality test FAILED with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting TTS functionality test...")
    test_result = test_tts_functionality()
    exit_code = 0 if test_result else 1
    exit(exit_code)
