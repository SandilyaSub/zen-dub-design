#!/usr/bin/env python3
"""
Demonstration script for the integrated speech processing functionality.
This script shows how to use the new SpeechProcessor class with VAD segmentation.
"""

import os
import json
import asyncio
import logging
import argparse
from dotenv import load_dotenv
from modules.speech_processor import SpeechProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def demo_speech_processing(
    audio_path: str,
    vad_enabled: bool = True,
    vad_threshold: float = 0.5,
    combine_duration: float = 8.0,
    combine_gap: float = 1.0,
    output_dir: str = "demo_outputs"
):
    """
    Demonstrate the speech processing functionality.
    
    Args:
        audio_path: Path to the audio file
        vad_enabled: Whether to use VAD segmentation
        vad_threshold: Threshold for VAD speech detection
        combine_duration: Maximum duration for combined segments
        combine_gap: Maximum gap between segments to combine
        output_dir: Directory to save results
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    logger.info(f"Processing audio file: {audio_path}")
    logger.info(f"VAD settings: enabled={vad_enabled}, threshold={vad_threshold}, "
                f"max_duration={combine_duration}s, max_gap={combine_gap}s")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize speech processor
    processor = SpeechProcessor()
    
    # Configure processor
    processor.configure(
        vad_config={
            "enabled": vad_enabled,
            "threshold": vad_threshold,
            "combine_duration": combine_duration,
            "combine_gap": combine_gap
        },
        diarization_config={
            "enabled": True,
            "model": "saarika:v2"
        },
        transcription_config={
            "model": "saarika:v2",
            "translate": False
        }
    )
    
    # Process audio
    try:
        start_time = asyncio.get_event_loop().time()
        results = await processor.process_audio(audio_path, output_dir)
        end_time = asyncio.get_event_loop().time()
        
        processing_time = end_time - start_time
        
        # Save formatted results
        formatted_path = os.path.join(output_dir, "formatted_results.json")
        with open(formatted_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        logger.info(f"Processing completed in {processing_time:.2f} seconds")
        logger.info(f"Results saved to: {formatted_path}")
        
        if results.get("success"):
            logger.info(f"Transcription: {results.get('transcription', '')[:100]}...")
            logger.info(f"Language: {results.get('language', 'unknown')}")
            logger.info(f"Number of segments: {len(results.get('segments', []))}")
            logger.info(f"Number of speakers: {len(results.get('speakers', {}))}")
            
            # Print speaker segments
            for i, segment in enumerate(results.get("segments", [])[:5]):
                logger.info(f"Segment {i+1}: {segment.get('speaker', 'unknown')} "
                           f"({segment.get('start', 0):.2f}s - {segment.get('end', 0):.2f}s): "
                           f"{segment.get('text', '')[:50]}...")
            
            if len(results.get("segments", [])) > 5:
                logger.info(f"... and {len(results.get('segments', [])) - 5} more segments")
        else:
            logger.error(f"Processing failed: {results.get('error', 'Unknown error')}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in speech processing demo: {e}")
        return None

def main():
    """Main function to parse arguments and run the demo."""
    parser = argparse.ArgumentParser(description="Demonstrate speech processing with VAD segmentation")
    parser.add_argument("audio_path", help="Path to the audio file")
    parser.add_argument("--disable-vad", action="store_true", help="Disable VAD segmentation")
    parser.add_argument("--vad-threshold", type=float, default=0.5, help="Threshold for VAD speech detection (0.0-1.0)")
    parser.add_argument("--combine-duration", type=float, default=8.0, help="Maximum duration for combined segments in seconds")
    parser.add_argument("--combine-gap", type=float, default=1.0, help="Maximum gap between segments to combine in seconds")
    parser.add_argument("--output-dir", default="demo_outputs", help="Directory to save results")
    
    args = parser.parse_args()
    
    asyncio.run(demo_speech_processing(
        audio_path=args.audio_path,
        vad_enabled=not args.disable_vad,
        vad_threshold=args.vad_threshold,
        combine_duration=args.combine_duration,
        combine_gap=args.combine_gap,
        output_dir=args.output_dir
    ))

if __name__ == "__main__":
    # If no arguments provided, use default audio path
    import sys
    if len(sys.argv) == 1:
        # Default audio path
        audio_path = "/Users/sandilya/Sandy/Startup Ideas/Speech Based/filmymojimiddleclassmadhu.mp3"
        logger.info(f"No audio path provided, using default: {audio_path}")
        asyncio.run(demo_speech_processing(audio_path))
    else:
        main()
