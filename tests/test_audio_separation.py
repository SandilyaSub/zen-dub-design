"""
Test script for audio separation functionality.

This script tests the audio_separator module by processing a sample audio file
and verifying that vocals and background are correctly separated.
"""

import os
import sys
import json
import argparse
from modules.audio_separator import separate_vocals_from_background, analyze_audio_components

def test_audio_separation(input_file, output_dir="test_outputs"):
    """
    Test audio separation on a given input file.
    
    Args:
        input_file (str): Path to the input audio file
        output_dir (str): Directory to save the separated audio files
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        return False
    
    # Create session ID from filename
    session_id = os.path.splitext(os.path.basename(input_file))[0]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Testing audio separation on: {input_file}")
    print(f"Session ID: {session_id}")
    print(f"Output directory: {output_dir}")
    
    # First analyze the audio components
    print("\n--- Audio Analysis ---")
    analysis = analyze_audio_components(input_file)
    print(f"Vocal score: {analysis.get('vocal_score', 'N/A')}")
    print(f"Music score: {analysis.get('music_score', 'N/A')}")
    print(f"Likely has vocals: {analysis.get('likely_has_vocals', 'N/A')}")
    print(f"Likely has music: {analysis.get('likely_has_music', 'N/A')}")
    
    # Perform separation
    print("\n--- Audio Separation ---")
    try:
        result = separate_vocals_from_background(input_file, output_dir, session_id)
        
        print(f"Separation complete!")
        print(f"Vocals saved to: {result['vocals_path']}")
        print(f"Background saved to: {result['background_path']}")
        print(f"Metadata saved to: {result['metadata_path']}")
        
        # Display metadata
        print("\n--- Separation Metadata ---")
        with open(result['metadata_path'], 'r') as f:
            metadata = json.load(f)
            
        print(f"Vocal percentage: {metadata['stats']['vocal_percentage']}%")
        print(f"Background percentage: {metadata['stats']['background_percentage']}%")
        print(f"Has significant background: {metadata['analysis']['has_significant_background']}")
        
        return True
    except Exception as e:
        print(f"Error during separation: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test audio separation functionality")
    parser.add_argument("input_file", help="Path to the input audio file")
    parser.add_argument("--output-dir", default="test_outputs", help="Directory to save the separated audio files")
    
    args = parser.parse_args()
    
    success = test_audio_separation(args.input_file, args.output_dir)
    
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1)
