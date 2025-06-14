#!/usr/bin/env python3
"""
Script to generate time-aligned TTS from diarization data.
This demonstrates the usage of the tts_time_aligner module.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import time-aligned TTS module
from modules.tts_time_aligner import time_aligned_tts

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Generate time-aligned TTS from diarization data')
    parser.add_argument('--diarization', required=True, help='Path to diarization JSON file with translations')
    parser.add_argument('--output', required=True, help='Path to save the output audio file')
    parser.add_argument('--language', required=True, help='Target language (e.g., hindi, english, telugu)')
    parser.add_argument('--provider', default='sarvam', choices=['sarvam', 'cartesia'], help='TTS provider to use')
    parser.add_argument('--voice', help='Voice ID to use')
    parser.add_argument('--bit-rate', type=int, default=128000, help='Audio bit rate (for Cartesia)')
    parser.add_argument('--sample-rate', type=int, default=44100, help='Audio sample rate (for Cartesia)')
    
    args = parser.parse_args()
    
    # Check if diarization file exists
    if not os.path.exists(args.diarization):
        logger.error(f"Diarization file not found: {args.diarization}")
        return 1
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    
    # Load diarization data
    with open(args.diarization, 'r', encoding='utf-8') as f:
        diarization_data = json.load(f)
    
    # Prepare options
    options = {
        'bit_rate': args.bit_rate,
        'sample_rate': args.sample_rate
    }
    
    # Generate time-aligned TTS
    success = time_aligned_tts(
        diarization_data=diarization_data,
        output_path=args.output,
        language=args.language,
        provider=args.provider,
        voice_id=args.voice,
        options=options
    )
    
    if success:
        logger.info(f"Successfully generated time-aligned TTS: {args.output}")
        return 0
    else:
        logger.error("Failed to generate time-aligned TTS")
        return 1

if __name__ == '__main__':
    sys.exit(main())
