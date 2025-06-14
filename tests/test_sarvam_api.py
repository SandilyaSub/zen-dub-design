#!/usr/bin/env python3
"""
Test script for Sarvam API integration with VAD.
"""
import os
import asyncio
import logging
from dotenv import load_dotenv
from modules.sarvam_speech import transcribe_with_vad_diarization

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Test the Sarvam API integration with VAD."""
    # Get API key from environment
    api_key = os.getenv('SARVAM_API_KEY')
    if not api_key:
        logger.error("SARVAM_API_KEY not found in environment variables")
        return
    
    # Test audio file path
    audio_path = "uploads/test_audio.mp3"
    if not os.path.exists(audio_path):
        logger.error(f"Test audio file not found: {audio_path}")
        return
    
    # Create output directory for VAD segments
    vad_segments_dir = "outputs/test/vad_segments"
    os.makedirs(vad_segments_dir, exist_ok=True)
    
    # Transcribe with VAD and diarization
    logger.info(f"Transcribing audio file: {audio_path}")
    results = await transcribe_with_vad_diarization(
        audio_path=audio_path,
        api_key=api_key,
        vad_segments_dir=vad_segments_dir,
        min_segment_duration=1.0
    )
    
    # Print results
    if "error" in results:
        logger.error(f"Error in transcription: {results['error']}")
    else:
        logger.info(f"Transcription successful!")
        logger.info(f"Transcript: {results.get('transcript', '')[:100]}...")
        logger.info(f"Number of segments: {len(results.get('segments', []))}")
        
        # Print first few segments
        for i, segment in enumerate(results.get('segments', [])[:3]):
            logger.info(f"Segment {i+1}: Speaker {segment.get('speaker')} - {segment.get('text')[:50]}...")

if __name__ == "__main__":
    asyncio.run(main())
