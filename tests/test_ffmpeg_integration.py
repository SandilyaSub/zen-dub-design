#!/usr/bin/env python3
"""
Test script to verify FFmpeg integration with the TTS processor.
This script tests basic audio operations using the bundled FFmpeg.
"""

import os
import logging
import tempfile
import subprocess
import warnings

# Import our patched module first to ensure FFmpeg is properly configured
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules import tts_processor

# Now import pydub which will use the patched configuration
from pydub import AudioSegment
import imageio_ffmpeg

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ffmpeg_integration():
    """Test basic audio operations using the bundled FFmpeg."""
    try:
        # Get FFmpeg path from our module
        ffmpeg_path = tts_processor.ffmpeg_path
        logger.info(f"Using FFmpeg from: {ffmpeg_path}")
        
        # Verify FFmpeg is working
        result = subprocess.run([ffmpeg_path, "-version"], 
                      check=True, capture_output=True, text=True)
        logger.info(f"FFmpeg version: {result.stdout.splitlines()[0]}")
        
        # Create a simple silent audio segment
        logger.info("Creating test audio segment...")
        silent_segment = AudioSegment.silent(duration=1000)  # 1 second of silence
        
        # Export to a temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_path = temp_file.name
        
        logger.info(f"Exporting audio to {output_path}...")
        silent_segment.export(output_path, format="wav")
        
        # Verify the file exists and has content
        file_size = os.path.getsize(output_path)
        logger.info(f"Generated audio file size: {file_size} bytes")
        
        if file_size > 0:
            logger.info("✅ FFmpeg integration test PASSED")
            return True
        else:
            logger.error("❌ FFmpeg integration test FAILED: Generated file is empty")
            return False
            
    except Exception as e:
        logger.error(f"❌ FFmpeg integration test FAILED with error: {str(e)}")
        return False
    finally:
        # Clean up
        if 'output_path' in locals() and os.path.exists(output_path):
            os.remove(output_path)
            logger.info(f"Removed temporary file: {output_path}")

if __name__ == "__main__":
    logger.info("Starting FFmpeg integration test...")
    test_result = test_ffmpeg_integration()
    exit_code = 0 if test_result else 1
    exit(exit_code)
