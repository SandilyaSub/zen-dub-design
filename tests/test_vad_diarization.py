#!/usr/bin/env python3
"""
Test script for VAD segmentation with Sarvam diarization.
This script demonstrates the enhanced diarization functionality using VAD segmentation.
"""

import os
import json
import asyncio
import logging
import argparse
from dotenv import load_dotenv
from modules.sarvam_speech import transcribe_with_vad_diarization

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

async def test_vad_diarization(audio_path, use_vad=True, vad_threshold=0.5, combine_duration=8, combine_gap=1):
    """
    Test the VAD segmentation with diarization functionality.
    
    Args:
        audio_path: Path to the audio file
        use_vad: Whether to use VAD segmentation
        vad_threshold: Threshold for VAD speech detection
        combine_duration: Maximum duration for combined segments
        combine_gap: Maximum gap between segments to combine
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    logger.info(f"Testing VAD diarization with audio file: {audio_path}")
    logger.info(f"VAD settings: enabled={use_vad}, threshold={vad_threshold}, max_duration={combine_duration}s, max_gap={combine_gap}s")
    
    # Create output directory
    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process with VAD diarization
    try:
        results = await transcribe_with_vad_diarization(
            audio_path=audio_path,
            api_key=SARVAM_API_KEY,
            use_vad=use_vad,
            vad_threshold=vad_threshold,
            combine_duration=combine_duration,
            combine_gap=combine_gap,
            temp_dir=os.path.join(output_dir, "vad_segments")
        )
        
        # Save the results to a file
        output_path = os.path.join(output_dir, "vad_diarization_output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_path}")
        
        # Print summary
        logger.info(f"Transcription completed with {len(results.get('segments', []))} segments")
        logger.info(f"Language: {results.get('language_code', 'unknown')}")
        logger.info(f"Transcript: {results.get('transcript', '')[:100]}...")
        
        # Count speakers
        speakers = set()
        for segment in results.get("segments", []):
            speakers.add(segment.get("speaker", "unknown"))
        
        logger.info(f"Detected {len(speakers)} speakers: {', '.join(speakers)}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in VAD diarization test: {e}")
        return None

def main():
    """Main function to parse arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test VAD segmentation with Sarvam diarization")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--disable-vad", action="store_true", help="Disable VAD segmentation")
    parser.add_argument("--vad-threshold", type=float, default=0.5, help="Threshold for VAD speech detection (0.0-1.0)")
    parser.add_argument("--combine-duration", type=float, default=8, help="Maximum duration for combined segments in seconds")
    parser.add_argument("--combine-gap", type=float, default=1, help="Maximum gap between segments to combine in seconds")
    
    args = parser.parse_args()
    
    asyncio.run(test_vad_diarization(
        audio_path=args.audio_path,
        use_vad=not args.disable_vad,
        vad_threshold=args.vad_threshold,
        combine_duration=args.combine_duration,
        combine_gap=args.combine_gap
    ))

if __name__ == "__main__":
    # If no arguments provided, use default audio path
    import sys
    if len(sys.argv) == 1:
        # Default audio path
        audio_path = "/Users/sandilya/Sandy/Startup Ideas/Speech Based/filmymojimiddleclassmadhu.mp3"
        logger.info(f"No audio path provided, using default: {audio_path}")
        asyncio.run(test_vad_diarization(audio_path))
    else:
        main()
