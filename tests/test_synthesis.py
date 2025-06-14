"""
Test script for TTS synthesis and logging.
"""

import os
import sys
import csv
import json
from pathlib import Path

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import our modules
from modules.tts_processor import TTSProcessor
from modules.synthesis_logger import SynthesisLogger
from utils.file_utils import ensure_dir

def main():
    # Create session directory in outputs folder
    session_id = "session_133scdv8j7fd"
    session_dir = os.path.join("outputs", session_id)
    os.makedirs(session_dir, exist_ok=True)
    os.makedirs(os.path.join(session_dir, "tts"), exist_ok=True)
    os.makedirs(os.path.join(session_dir, "synthesis"), exist_ok=True)
    
    # Create test data file
    test_data_path = os.path.join(session_dir, "test_data.json")
    
    # Create temporary JSON file with test data
    test_data = {
        "segments": [
            {
                "segment_id": 0,
                "speaker": "SPEAKER_00",
                "start_time": 0.522,
                "end_time": 6.512,
                "duration": 5.99,
                "text": "हेलो मैं यूलू से अर्पिता बात कर रही हूँ। मैंने देखा कि आपने रेंटल प्लान नहीं खरीदा।",
                "translated_text": "Hello, I'm Arpita from Yulu. I noticed you haven't purchased a rental plan.",
                "gender": "M",
                "pace": 1
            },
            {
                "segment_id": 1,
                "speaker": "SPEAKER_00",
                "start_time": 6.826,
                "end_time": 8.726,
                "duration": 1.9,
                "text": "क्या आप मुझे बता सकते हैं कि क्या हुआ?",
                "translated_text": "Can you tell me what happened?",
                "gender": "M",
                "pace": 1
            }
        ],
        "target_language": "english"
    }
    
    with open(test_data_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # Initialize processor with session directory
    processor = TTSProcessor(session_id="session_133scdv8j7fd", output_dir=session_dir)
    
    # Process TTS
    output_file = processor.process_tts(test_data_path)
    
    print(f"\nProcessing completed successfully!")
    print(f"Final audio saved to: {output_file}")
    print(f"Synthesis details saved to: {os.path.join(session_dir, 'synthesis', f'synthesis_details_{session_id}.json')}")

if __name__ == "__main__":
    main()
