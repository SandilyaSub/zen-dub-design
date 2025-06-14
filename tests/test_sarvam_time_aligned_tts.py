#!/usr/bin/env python3
"""
Test Time-Aligned TTS with Multiple Providers
===========================================

Objective:
---------
This script provides a standalone way to test the time-aligned TTS process using multiple TTS providers
(Sarvam or Cartesia) for any diarization_translated_merged.json file. It allows testing different voice 
combinations and time alignment settings without modifying the main application code.

What it does:
-----------
1. Processes each merged segment using the selected TTS provider with specified speaker voices
2. Applies time alignment to match original segment durations
3. Stitches the segments together with precise timing at original start times
4. Adds background music if provided
5. Saves the final output to the test_outputs directory

Syntax:
------
python3 test_time_aligned_tts.py \
    --merged_file /path/to/diarization_translated_merged.json \
    --model [sarvam|cartesia] \
    --api_key YOUR_API_KEY \
    [--background_music /path/to/background.wav] \
    [--original_audio /path/to/original.wav] \
    [--output_name custom_output_name] \
    [--speaker_0 voice_id] \
    [--speaker_1 voice_id] \
    [--speaker_2 voice_id] \
    [--speaker_3 voice_id] \
    [--default voice_id] \
    [--use_mock]

Sample Commands:
--------------
# Using Sarvam TTS
python3 tests/test_time_aligned_tts.py \
    --merged_file /path/to/diarization_translated_merged.json \
    --model sarvam \
    --api_key YOUR_SARVAM_API_KEY \
    --speaker_0 abhilash --speaker_1 karun

# Using Cartesia TTS
python3 tests/test_time_aligned_tts.py \
    --merged_file /path/to/diarization_translated_merged.json \
    --model cartesia \
    --api_key YOUR_CARTESIA_API_KEY \
    --speaker_0 Vaishnavi --speaker_1 Sandilya

# With background music and original audio
python3 tests/test_time_aligned_tts.py \
    --merged_file /path/to/diarization_translated_merged.json \
    --model sarvam \
    --background_music /path/to/background.wav \
    --original_audio /path/to/original.wav \
    --api_key YOUR_API_KEY

# Using mock TTS for testing without API key
python3 tests/test_time_aligned_tts.py \
    --merged_file /path/to/diarization_translated_merged.json \
    --model sarvam \
    --use_mock
"""

import os
import sys
import json
import argparse
import logging
import shutil
import tempfile
import subprocess
import wave
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from modules.sarvam_tts import synthesize_speech as sarvam_synthesize, get_available_voices as get_sarvam_voices
from modules.cartesia_tts import synthesize_speech as cartesia_synthesize, get_available_voices as get_cartesia_voices
from modules.time_aligned_tts import (
    adjust_segment_duration,
    process_segments_with_time_alignment,
    stitch_time_aligned_segments
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join('test_outputs', 'sarvam_tts_test.log'))
    ]
)
logger = logging.getLogger(__name__)

def setup_test_directories(output_name: str) -> Dict[str, str]:
    """
    Set up the necessary directories for the test.
    
    Args:
        output_name: Name for the output directory
        
    Returns:
        Dict: Dictionary of paths for the test
    """
    # Create base test output directory
    test_output_dir = os.path.join('test_outputs', output_name)
    os.makedirs(test_output_dir, exist_ok=True)
    
    # Create subdirectories
    tts_dir = os.path.join(test_output_dir, 'tts')
    synthesis_dir = os.path.join(test_output_dir, 'synthesis')
    audio_dir = os.path.join(test_output_dir, 'audio')
    
    os.makedirs(tts_dir, exist_ok=True)
    os.makedirs(synthesis_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    # Return paths dictionary
    return {
        'test_output_dir': test_output_dir,
        'tts_dir': tts_dir,
        'synthesis_dir': synthesis_dir,
        'audio_dir': audio_dir
    }

def load_merged_segments(merged_file_path: str) -> Dict[str, Any]:
    """
    Load the merged segments from the diarization_translated_merged.json file.
    
    Args:
        merged_file_path: Path to the merged segments file
        
    Returns:
        Dict: The merged segments data
    """
    if not os.path.exists(merged_file_path):
        logger.error(f"Merged segments file not found: {merged_file_path}")
        sys.exit(1)
    
    try:
        with open(merged_file_path, 'r') as f:
            merged_data = json.load(f)
        logger.info(f"Loaded merged segments from {merged_file_path}")
        return merged_data
    except Exception as e:
        logger.error(f"Error loading merged segments: {e}")
        sys.exit(1)

def generate_mock_speech(text: str, output_path: str, duration: float = None, model: str = 'sarvam') -> bool:
    """
    Generate a mock speech file for testing without API access.
    
    Args:
        text: The text to synthesize
        output_path: Path to save the synthesized audio
        duration: Duration of the audio in seconds (if None, will be based on text length)
        model: TTS model being mocked ('sarvam' or 'cartesia')
        
    Returns:
        bool: Success status
    """
    try:
        # Calculate duration based on text length if not provided
        if duration is None:
            # Rough estimate: 3 characters per second
            duration = max(1.0, len(text) / 3)  
        
        # Generate a simple sine wave
        sample_rate = 22050
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Generate a tone that varies slightly based on text hash to simulate different voices
        text_hash = sum(ord(c) for c in text) % 10
        freq = 220 + (text_hash * 20)  # Vary frequency based on text
        
        # Create a simple sine wave with amplitude modulation
        sine = np.sin(2 * np.pi * freq * t) * 0.5
        
        # Add some variation
        modulation = np.sin(2 * np.pi * 2 * t) * 0.1
        audio = (sine + modulation) * 32767  # Scale to 16-bit range
        
        # Convert to int16
        audio = audio.astype(np.int16)
        
        # Save as WAV file
        with wave.open(output_path, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())
        
        logger.info(f"Generated mock speech file: {output_path} (duration: {duration:.2f}s)")
        return True
    except Exception as e:
        logger.error(f"Error generating mock speech: {e}")
        return False

def synthesize_segment(
    segment: Dict[str, Any],
    speaker_voice_map: Dict[str, str],
    output_dir: str,
    model: str = 'sarvam',
    api_key: str = None,
    use_mock: bool = False
) -> Optional[str]:
    """
    Synthesize a single segment using the specified TTS model or mock TTS.
    
    Args:
        segment: The segment to synthesize
        speaker_voice_map: Mapping of speaker IDs to voice IDs
        output_dir: Directory to save the synthesized audio
        model: TTS model to use ('sarvam' or 'cartesia')
        api_key: API key for the TTS service (optional)
        use_mock: Whether to use mock TTS instead of actual TTS service
        
    Returns:
        str: Path to the synthesized audio file, or None if synthesis failed
    """
    segment_id = segment.get('segment_id')
    speaker = segment.get('speaker', 'SPEAKER_00')
    text = segment.get('translated_text', '')
    language = segment.get('language', 'hindi')
    duration = segment.get('duration', 0)
    
    if not text:
        logger.warning(f"No translated text found for segment {segment_id}")
        return None
    
    # Get voice ID for this speaker
    voice_id = speaker_voice_map.get(speaker, speaker_voice_map.get('default'))
    if not voice_id and not use_mock:
        logger.warning(f"No voice ID found for speaker {speaker}, using first available voice")
        if model.lower() == 'sarvam':
            available_voices = get_sarvam_voices()
        else:  # cartesia
            available_voices = get_cartesia_voices()
            
        if available_voices:
            voice_id = available_voices[0]['id']
        else:
            logger.error(f"No voices available for {model} TTS")
            return None
    
    # Create output path
    output_path = os.path.join(output_dir, f"segment_{segment_id}.wav")
    
    # Use mock TTS if requested or if no API key is available
    if use_mock:
        logger.info(f"Generating mock speech for segment {segment_id} with speaker {speaker}")
        success = generate_mock_speech(text, output_path, duration, model=model)
    else:
        # Set environment variable for API key if provided
        if api_key:
            if model.lower() == 'sarvam':
                os.environ['SARVAM_API_KEY'] = api_key
            else:  # cartesia
                os.environ['CARTESIA_API_KEY'] = api_key
        
        logger.info(f"Synthesizing segment {segment_id} with {model} TTS using voice {voice_id}")
        
        # Synthesize speech with appropriate TTS engine
        if model.lower() == 'sarvam':
            success = sarvam_synthesize(
                text=text,
                language=language,
                output_path=output_path,
                speaker=voice_id,
                pitch=0,
                pace=1.0,  # Default pace, will be adjusted in time alignment
                loudness=1.0
            )
        else:  # cartesia
            success = cartesia_synthesize(
                text=text,
                output_path=output_path,
                voice_id=voice_id
            )
    
    if success:
        logger.info(f"Successfully synthesized segment {segment_id} with {model} TTS")
        return output_path
    else:
        logger.error(f"Failed to synthesize segment {segment_id} with {model} TTS")
        return None

def process_all_segments(
    merged_data: Dict[str, Any],
    speaker_voice_map: Dict[str, str],
    paths: Dict[str, str],
    model: str = 'sarvam',
    api_key: str = None,
    use_mock: bool = False
) -> List[Dict[str, Any]]:
    """
    Process all segments in the merged data.
    
    Args:
        merged_data: The merged segments data
        speaker_voice_map: Mapping of speaker IDs to voice IDs
        paths: Dictionary of paths for the test
        
    Returns:
        List: List of processed segments with synthesis information
    """
    merged_segments = merged_data.get('merged_segments', [])
    processed_segments = []
    
    for segment in merged_segments:
        segment_output = synthesize_segment(segment, speaker_voice_map, paths['tts_dir'], model, api_key, use_mock)
        
        if segment_output:
            segment_info = {
                'segment_id': segment.get('segment_id'),
                'speaker': segment.get('speaker', 'SPEAKER_00'),
                'voice_id': speaker_voice_map.get(segment.get('speaker', 'SPEAKER_00'), speaker_voice_map.get('default')),
                'original_duration': segment.get('duration', 0),
                'tts_file': segment_output,
                'status': 'success'
            }
            processed_segments.append(segment_info)
        else:
            segment_info = {
                'segment_id': segment.get('segment_id'),
                'speaker': segment.get('speaker', 'SPEAKER_00'),
                'status': 'failed'
            }
            processed_segments.append(segment_info)
    
    return processed_segments

def run_time_alignment(
    output_name: str,
    processed_segments: List[Dict[str, Any]],
    paths: Dict[str, str],
    merged_data_path: str
) -> Dict[str, Any]:
    """
    Run the time alignment process on the synthesized segments.
    
    Args:
        output_name: Name for the output directory
        processed_segments: List of processed segments with synthesis information
        paths: Dictionary of paths for the test
        merged_data_path: Path to the merged data file
        
    Returns:
        Dict: Metadata about the time alignment process
    """
    # Create a temporary metadata file for the time alignment process
    temp_metadata_path = os.path.join(paths['synthesis_dir'], 'temp_segments.json')
    
    with open(temp_metadata_path, 'w') as f:
        json.dump(processed_segments, f, indent=2)
    
    # Set up paths for time alignment
    alignment_metadata_path = os.path.join(paths['synthesis_dir'], 'time_alignment_metadata.json')
    
    # Process segments with time alignment
    alignment_metadata = process_segments_with_time_alignment(
        session_id=output_name,  # Using output_name as session_id for organization
        output_dir='test_outputs',
        vad_segments_file=merged_data_path,
        tts_dir=paths['tts_dir'],
        metadata_output_path=alignment_metadata_path
    )
    
    logger.info(f"Time alignment complete, metadata saved to {alignment_metadata_path}")
    return alignment_metadata

def stitch_segments(
    output_name: str,
    alignment_metadata: Dict[str, Any],
    paths: Dict[str, str],
    original_audio_path: Optional[str] = None,
    background_music_path: Optional[str] = None,
    enable_background_music: bool = True
) -> str:
    """
    Stitch the time-aligned segments together.
    
    Args:
        output_name: Name for the output directory
        alignment_metadata: Metadata about the time alignment process
        paths: Dictionary of paths for the test
        original_audio_path: Path to the original audio file (optional)
        background_music_path: Path to the background music file (optional)
        enable_background_music: Whether to enable background music
        
    Returns:
        str: Path to the final stitched audio file
    """
    # Set up output path for the final audio
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_output_path = os.path.join(paths['synthesis_dir'], f"final_output_time_aligned_{timestamp}.wav")
    
    # Create music directory and copy background music if provided
    if background_music_path and os.path.exists(background_music_path) and enable_background_music:
        music_dir = os.path.join(paths['test_output_dir'], 'music')
        os.makedirs(music_dir, exist_ok=True)
        
        # Copy background music file
        background_copy = os.path.join(music_dir, 'background.wav')
        shutil.copy2(background_music_path, background_copy)
        logger.info(f"Copied background music to {background_copy}")
        
        # Create metadata file to enable background music
        metadata = {
            "analysis": {
                "has_significant_background": True
            },
            "stats": {
                "vocals_rms_db": -20,
                "background_rms_db": -30
            }
        }
        
        with open(os.path.join(music_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create user metadata file to enable background music preference
        user_metadata = {
            "preserve_background_music": enable_background_music
        }
        
        with open(os.path.join(paths['test_output_dir'], 'metadata.json'), 'w') as f:
            json.dump(user_metadata, f, indent=2)
    
    # Stitch segments
    output_path = stitch_time_aligned_segments(
        session_id=output_name,  # Using output_name as session_id for organization
        output_dir='test_outputs',
        alignment_metadata=alignment_metadata,
        output_file=final_output_path,
        original_audio_path=original_audio_path
    )
    
    if output_path:
        logger.info(f"Successfully stitched segments, final output saved to {output_path}")
        return output_path
    else:
        logger.error("Failed to stitch segments")
        return None

def main():
    """Main function to run the test."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Time-Aligned TTS with multiple providers')
    parser.add_argument('--merged_file', required=True, help='Path to diarization_translated_merged.json file')
    parser.add_argument('--model', choices=['sarvam', 'cartesia'], default='sarvam', 
                        help='TTS model to use (sarvam or cartesia)')
    parser.add_argument('--original_audio', help='Path to original audio file (optional)')
    parser.add_argument('--background_music', help='Path to background music file (optional)')
    parser.add_argument('--disable_background', action='store_true', help='Disable background music even if provided')
    parser.add_argument('--output_name', help='Name for output directory (defaults to timestamp)')
    parser.add_argument('--speaker_0', help='Voice ID for SPEAKER_00')
    parser.add_argument('--speaker_1', help='Voice ID for SPEAKER_01')
    parser.add_argument('--speaker_2', help='Voice ID for SPEAKER_02')
    parser.add_argument('--speaker_3', help='Voice ID for SPEAKER_03')
    parser.add_argument('--default', help='Default voice ID for unknown speakers')
    parser.add_argument('--api_key', help='API key for the selected TTS service')
    parser.add_argument('--use_mock', action='store_true', help='Use mock TTS instead of actual TTS service')
    
    args = parser.parse_args()
    
    # Set default voice IDs based on the selected model
    if args.model.lower() == 'sarvam':
        speaker_0_default = 'anushka'
        speaker_1_default = 'abhilash'
        speaker_2_default = 'karun'
        speaker_3_default = 'vidya'
        default_default = 'manisha'
    else:  # cartesia
        speaker_0_default = 'Vaishnavi'
        speaker_1_default = 'Sandilya'
        speaker_2_default = 'Madhu'
        speaker_3_default = 'Budatha'
        default_default = 'Mahesh'
    
    # Create speaker-voice mapping with defaults if not provided
    speaker_voice_map = {
        'SPEAKER_00': args.speaker_0 if args.speaker_0 else speaker_0_default,
        'SPEAKER_01': args.speaker_1 if args.speaker_1 else speaker_1_default,
        'SPEAKER_02': args.speaker_2 if args.speaker_2 else speaker_2_default,
        'SPEAKER_03': args.speaker_3 if args.speaker_3 else speaker_3_default,
        'default': args.default if args.default else default_default
    }
    
    # Generate output name if not provided
    output_name = args.output_name
    if not output_name:
        output_name = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create test output directory
    os.makedirs('test_outputs', exist_ok=True)
    
    # Set up test directories
    paths = setup_test_directories(output_name)
    
    # Load merged segments
    merged_data = load_merged_segments(args.merged_file)
    
    # Copy the merged file to the test output directory for reference
    merged_file_copy = os.path.join(paths['test_output_dir'], 'diarization_translated_merged.json')
    shutil.copy2(args.merged_file, merged_file_copy)
    
    # Process all segments
    logger.info(f"Processing {len(merged_data.get('merged_segments', []))} segments with {args.model} TTS")
    processed_segments = process_all_segments(
        merged_data, 
        speaker_voice_map, 
        paths, 
        model=args.model,
        api_key=args.api_key, 
        use_mock=args.use_mock
    )
    
    # Run time alignment
    logger.info("Running time alignment")
    alignment_metadata = run_time_alignment(output_name, processed_segments, paths, merged_file_copy)
    
    # Copy original audio if provided
    original_audio_path = None
    if args.original_audio and os.path.exists(args.original_audio):
        original_audio_copy = os.path.join(paths['audio_dir'], os.path.basename(args.original_audio))
        shutil.copy2(args.original_audio, original_audio_copy)
        original_audio_path = original_audio_copy
        logger.info(f"Copied original audio to {original_audio_copy}")
    
    # Stitch segments
    logger.info("Stitching segments")
    final_output_path = stitch_segments(
        output_name, 
        alignment_metadata, 
        paths, 
        original_audio_path,
        args.background_music,
        not args.disable_background
    )
    
    if final_output_path:
        logger.info(f"Test completed successfully. Final output: {final_output_path}")
        print(f"\nTest completed successfully!\nFinal output: {final_output_path}")
    else:
        logger.error("Test failed")
        print("\nTest failed. Check logs for details.")

if __name__ == "__main__":
    main()
