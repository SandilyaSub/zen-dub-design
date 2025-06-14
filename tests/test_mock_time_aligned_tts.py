#!/usr/bin/env python3
"""
Mock test for the time-aligned TTS functionality.
This script creates a mock version of the TTS providers to test the time-aligned TTS logic.
"""

import os
import sys
import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
from pydub import AudioSegment

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from modules.tts_time_aligner import time_aligned_tts

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_diarization_data():
    """Create a sample diarization JSON with translations for testing."""
    
    # Sample diarization data with translations
    data = {
        "request_id": "test_request",
        "language_code": "hi",  # Hindi
        "transcript": "नमस्ते, मेरा नाम राम है। मैं भारत से हूँ। आप कैसे हैं?",
        "translated_transcript": "Hello, my name is Ram. I am from India. How are you?",
        "segments": [
            {
                "segment_id": "seg_001",
                "speaker": "speaker_1",
                "start_time": 1.0,
                "end_time": 3.5,
                "text": "Hello, my name is Ram."
            },
            {
                "segment_id": "seg_002",
                "speaker": "speaker_1",
                "start_time": 4.5,
                "end_time": 6.0,
                "text": "I am from India."
            },
            {
                "segment_id": "seg_003",
                "speaker": "speaker_1",
                "start_time": 7.0,
                "end_time": 8.5,
                "text": "How are you?"
            }
        ]
    }
    
    return data

def create_mock_audio(duration_seconds=1.0, sample_rate=44100):
    """Create a mock audio segment of the specified duration."""
    # Create a silent audio segment
    audio = AudioSegment.silent(duration=int(duration_seconds * 1000), frame_rate=sample_rate)
    return audio

def mock_sarvam_synthesize_speech(*args, **kwargs):
    """Mock function for Sarvam TTS synthesis."""
    # Extract text and output path from kwargs
    text = kwargs.get('text', '')
    output_path = kwargs.get('output_path', '')
    
    # Create a mock audio file with duration proportional to text length
    # This simulates the behavior of TTS generating longer audio for longer text
    duration = len(text) * 0.05  # Roughly 50ms per character
    audio = create_mock_audio(duration_seconds=duration)
    
    # Save the mock audio to the output path
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    audio.export(output_path, format="wav")
    
    return True

def mock_cartesia_synthesize_speech(*args, **kwargs):
    """Mock function for Cartesia TTS synthesis."""
    # Extract text, output path, and duration from kwargs
    text = args[0] if args else kwargs.get('text', '')
    output_path = args[1] if len(args) > 1 else kwargs.get('output_path', '')
    duration = kwargs.get('duration', None)
    
    # If duration is specified, use it; otherwise, calculate based on text length
    if duration is None:
        duration = len(text) * 0.05  # Roughly 50ms per character
    
    # Create a mock audio file
    audio = create_mock_audio(duration_seconds=duration)
    
    # Save the mock audio to the output path
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    audio.export(output_path, format="mp3")
    
    return True

@patch('modules.sarvam_tts.synthesize_speech', side_effect=mock_sarvam_synthesize_speech)
@patch('modules.cartesia_tts.synthesize_speech', side_effect=mock_cartesia_synthesize_speech)
def test_time_aligned_tts_with_mocks(mock_cartesia, mock_sarvam):
    """Test time-aligned TTS with mock TTS providers."""
    
    # Create sample diarization data
    diarization_data = create_sample_diarization_data()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Test Sarvam TTS
    logger.info("Testing Sarvam time-aligned TTS with mocks...")
    sarvam_output = os.path.join(output_dir, "mock_sarvam_time_aligned.wav")
    sarvam_success = time_aligned_tts(
        diarization_data=diarization_data,
        output_path=sarvam_output,
        language="english",
        provider="sarvam",
        voice_id="meera"
    )
    
    # Test Cartesia TTS
    logger.info("Testing Cartesia time-aligned TTS with mocks...")
    cartesia_output = os.path.join(output_dir, "mock_cartesia_time_aligned.mp3")
    cartesia_success = time_aligned_tts(
        diarization_data=diarization_data,
        output_path=cartesia_output,
        language="hindi",
        provider="cartesia",
        voice_id=None,
        options={
            "bit_rate": 128000,
            "sample_rate": 44100
        }
    )
    
    # Print summary
    logger.info("\n--- Test Summary ---")
    logger.info(f"Sarvam TTS: {'Success' if sarvam_success else 'Failed'}")
    if sarvam_success:
        logger.info(f"Sarvam output: {sarvam_output}")
    
    logger.info(f"Cartesia TTS: {'Success' if cartesia_success else 'Failed'}")
    if cartesia_success:
        logger.info(f"Cartesia output: {cartesia_output}")
    
    return sarvam_success, cartesia_success

def main():
    """Main function to run the tests."""
    
    # Test with mocks
    sarvam_success, cartesia_success = test_time_aligned_tts_with_mocks()
    
    return 0 if sarvam_success or cartesia_success else 1

if __name__ == '__main__':
    sys.exit(main())
