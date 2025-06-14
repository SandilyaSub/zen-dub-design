#!/usr/bin/env python3
"""
Create a merged file for TTS testing from a translated diarization file.
This script takes a translated diarization file and creates a merged file
that can be used for TTS testing.
"""

import os
import sys
import json
import argparse
from datetime import datetime

def create_merged_file(translated_file_path, output_path=None):
    """
    Create a merged file for TTS testing from a translated diarization file.
    
    Args:
        translated_file_path: Path to the translated diarization file
        output_path: Path to save the merged file (optional)
        
    Returns:
        str: Path to the created merged file
    """
    # Load the translated file
    with open(translated_file_path, 'r', encoding='utf-8') as f:
        translated_data = json.load(f)
    
    # Create the merged data structure
    merged_data = {
        "merged_segments": []
    }
    
    # Process each segment
    for segment in translated_data.get("segments", []):
        merged_segment = {
            "segment_id": segment.get("segment_id"),
            "speaker": segment.get("speaker", "SPEAKER_00"),
            "start_time": segment.get("start_time"),
            "end_time": segment.get("end_time"),
            "duration": segment.get("end_time", 0) - segment.get("start_time", 0),
            "text": segment.get("text", ""),
            "translated_text": segment.get("translated_text", ""),
            "language": translated_data.get("translation_info", {}).get("target_language", "telugu")
        }
        merged_data["merged_segments"].append(merged_segment)
    
    # Add metadata
    merged_data["metadata"] = {
        "source_language": translated_data.get("translation_info", {}).get("source_language", "hindi"),
        "target_language": translated_data.get("translation_info", {}).get("target_language", "telugu"),
        "timestamp": datetime.now().isoformat(),
        "created_by": "create_merged_file.py"
    }
    
    # Generate output path if not provided
    if not output_path:
        output_dir = os.path.dirname(translated_file_path)
        filename = os.path.basename(translated_file_path).replace("_translated_", "_merged_")
        output_path = os.path.join(output_dir, filename)
    
    # Save the merged file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created merged file: {output_path}")
    return output_path

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Create a merged file for TTS testing')
    parser.add_argument('--translated_file', required=True, help='Path to the translated diarization file')
    parser.add_argument('--output_file', help='Path to save the merged file (optional)')
    
    args = parser.parse_args()
    
    create_merged_file(args.translated_file, args.output_file)

if __name__ == "__main__":
    main()
