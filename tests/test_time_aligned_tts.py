#!/usr/bin/env python3
"""
Test Time-Aligned TTS with Multiple Providers
===========================================

Objective:
---------
This script provides a standalone way to test the time-aligned TTS process using multiple TTS providers
(Sarvam, Cartesia, or OpenAI) for any diarization_translated_merged.json file. It allows testing different voice 
combinations and time alignment settings without modifying the main application code.

What it does:
-----------
1. Processes each merged segment using the selected TTS provider with specified speaker voices
2. Applies time alignment to match original segment durations
3. Stitches the segments together with precise timing at original start times
4. Adds background music if provided
5. Saves the final output to the test_outputs directory

Usage Modes:
-----------
This script can be used in two modes:

1. **New Test Mode**: Creates a new test run with the specified merged file
2. **Existing Session Mode**: Uses an existing session ID to work with files already in place

The Existing Session Mode is useful for debugging or reprocessing existing sessions without
needing to recreate all the files. It automatically finds all required files based on the session ID.

Voice Selection:
--------------
For all providers, you can specify human-readable voice names:

- Sarvam voices: abhilash, anushka, karun, vidya, manisha, etc.
- Cartesia voices: Vaishnavi, Sandilya, Madhu, Budatha, Mahesh, Balli, etc.
- OpenAI voices: alloy, echo, fable, onyx, nova, shimmer, etc.

The script will automatically map these voice names to the appropriate voice IDs for each provider.

Syntax:
------
# New Test Mode
python3 test_time_aligned_tts.py \
    --merged_file /path/to/diarization_translated_merged.json \
    --model [sarvam|cartesia|openai] \
    --api_key YOUR_API_KEY \
    [--background_music /path/to/background.wav] \
    [--original_audio /path/to/original.wav] \
    [--output_name custom_output_name] \
    [--speaker_0 voice_name] \
    [--speaker_1 voice_name] \
    [--speaker_2 voice_name] \
    [--speaker_3 voice_name] \
    [--default voice_name] \
    [--use_mock]

# Existing Session Mode
python3 test_time_aligned_tts.py \
    --session_id YOUR_SESSION_ID \
    --model [sarvam|cartesia|openai] \
    --api_key YOUR_API_KEY \
    [--background_music /path/to/background.wav] \
    [--disable_background_music] \
    [--speaker_0 voice_name] \
    [--speaker_1 voice_name] \
    [--speaker_2 voice_name] \
    [--speaker_3 voice_name] \
    [--default voice_name] \
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
import time
import math
import shutil
import logging
import wave
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from pydub import AudioSegment
import datetime
import math

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import TTS modules
from modules.sarvam_tts import synthesize_speech as sarvam_synthesize, get_available_voices as get_sarvam_voices
from modules.cartesia_tts import synthesize_speech as cartesia_synthesize, get_available_voices as get_cartesia_voices
from modules.openai_tts import synthesize_speech as openai_synthesize
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

def setup_test_directories(output_name: str, is_existing_session: bool = False) -> Dict[str, str]:
    """
    Set up the necessary directories for the test.
    
    Args:
        output_name: Name for the output directory or session ID
        is_existing_session: Whether this is an existing session
        
    Returns:
        Dict: Dictionary of paths for the test
    """
    if is_existing_session:
        # For existing sessions, try both outputs and test_outputs directories
        session_name = output_name if output_name.startswith('session_') else f'session_{output_name}'
        
        # First try test_outputs directory
        base_output_dir = 'test_outputs'
        session_dir = os.path.join(base_output_dir, session_name)
        
        # If not found, try the original outputs directory
        if not os.path.exists(session_dir):
            base_output_dir = 'outputs'
            session_dir = os.path.join(base_output_dir, session_name)
            
            # If still not found, create a new session in test_outputs
            if not os.path.exists(session_dir):
                logger.info(f"Session directory not found, creating new session in test_outputs: {session_name}")
                
                # Check if we can find a reference session to copy from
                reference_session = 'session_bq3n044126'  # Use a known good session as reference
                reference_dir = os.path.join('outputs', reference_session)
                
                # Create the new session directory
                base_output_dir = 'test_outputs'
                session_dir = os.path.join(base_output_dir, session_name)
                os.makedirs(session_dir, exist_ok=True)
                
                # Create subdirectories
                for subdir in ['tts', 'synthesis', 'audio']:
                    os.makedirs(os.path.join(session_dir, subdir), exist_ok=True)
                
                # Copy the merged file from the reference session if it exists
                if os.path.exists(reference_dir):
                    reference_merged_file = os.path.join(reference_dir, 'diarization_translated_merged.json')
                    if os.path.exists(reference_merged_file):
                        import shutil
                        new_merged_file = os.path.join(session_dir, 'diarization_translated_merged.json')
                        shutil.copy2(reference_merged_file, new_merged_file)
                        logger.info(f"Copied reference merged file to new session: {new_merged_file}")
                        
                        # Also copy any needed audio files
                        if os.path.exists(os.path.join(reference_dir, 'synthesis')):
                            for file in os.listdir(os.path.join(reference_dir, 'synthesis')):
                                if file.endswith('.wav') and 'time_aligned' in file:
                                    src = os.path.join(reference_dir, 'synthesis', file)
                                    dst = os.path.join(session_dir, 'synthesis', file)
                                    shutil.copy2(src, dst)
                                    logger.info(f"Copied audio file: {file}")
                                    
                        # Create music directory if needed
                        os.makedirs(os.path.join(session_dir, 'music'), exist_ok=True)
        
        # Define paths based on existing session structure
        test_output_dir = session_dir
        tts_dir = os.path.join(test_output_dir, 'tts')
        synthesis_dir = os.path.join(test_output_dir, 'synthesis')
        audio_dir = os.path.join(test_output_dir, 'audio')
        
        logger.info(f"Using existing session directory: {test_output_dir}")
    else:
        # For new test runs, always create a new directory in test_outputs
        base_output_dir = 'test_outputs'
        test_output_dir = os.path.join(base_output_dir, output_name)
        os.makedirs(test_output_dir, exist_ok=True)
        
        # Create subdirectories
        tts_dir = os.path.join(test_output_dir, 'tts')
        synthesis_dir = os.path.join(test_output_dir, 'synthesis')
        audio_dir = os.path.join(test_output_dir, 'audio')
        
        os.makedirs(tts_dir, exist_ok=True)
        os.makedirs(synthesis_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        
        logger.info(f"Created new test directory: {test_output_dir}")
    
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

def generate_mock_speech(
    text: str,
    output_path: str,
    duration: float = None,
    model: str = 'sarvam'
) -> bool:
    """
    Generate a mock speech file for testing without API access.
    
    Args:
        text: The text to synthesize
        output_path: Path to save the synthesized audio
        duration: Duration of the audio in seconds (if None, will be based on text length)
        model: TTS model being mocked ('sarvam', 'cartesia', or 'openai')
        
    Returns:
        bool: Success status
    """
    try:
        # Calculate duration based on text length if not provided
        if duration is None:
            # Estimate: average speaking rate is about 150 words per minute
            # So about 2.5 words per second
            word_count = len(text.split())
            duration = max(1.0, word_count / 2.5)  # At least 1 second
        
        # Create a silent audio segment of the specified duration
        sample_rate = 16000
        num_samples = int(duration * sample_rate)
        
        # Generate a simple tone instead of silence
        t = np.linspace(0, duration, num_samples, False)
        
        # Different tones for different models
        if model.lower() == 'sarvam':
            # 440 Hz tone (A4) for Sarvam
            frequency = 440
        elif model.lower() == 'cartesia':
            # 523 Hz tone (C5) for Cartesia
            frequency = 523
        else:  # openai
            # 660 Hz tone (E5) for OpenAI
            frequency = 660
        
        # Generate a simple sine wave
        tone = np.sin(2 * np.pi * frequency * t) * 0.3  # 0.3 to reduce volume
        
        # Add some noise to make it sound more like speech
        noise = np.random.normal(0, 0.01, num_samples)
        audio_data = tone + noise
        
        # Add some amplitude modulation to simulate speech patterns
        modulation = 0.5 + 0.5 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz modulation
        audio_data = audio_data * modulation
        
        # Normalize to 16-bit range
        audio_data = np.int16(audio_data / np.max(np.abs(audio_data)) * 32767)
        
        # Save as WAV file
        import wave
        with wave.open(output_path, 'w') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        logger.info(f"Generated mock speech file at {output_path} with duration {duration:.2f} seconds for {model} model")
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
        model: TTS model to use ('sarvam', 'cartesia', or 'openai')
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
    
    # Get voice name for this speaker
    voice_name = speaker_voice_map.get(speaker, speaker_voice_map.get('default'))
    if not voice_name and not use_mock:
        logger.warning(f"No voice name found for speaker {speaker}, using first available voice")
        if model.lower() == 'sarvam':
            available_voices = get_sarvam_voices()
        elif model.lower() == 'cartesia':
            available_voices = get_cartesia_voices()
        else:  # openai
            # For OpenAI, we'll use the default voice
            voice_name = 'Madhu'
            available_voices = [{'name': voice_name}]
            
        if available_voices:
            voice_name = available_voices[0]['name']
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
                logger.info(f"Set SARVAM_API_KEY environment variable with length {len(api_key)}")
            elif model.lower() == 'cartesia':
                os.environ['CARTESIA_API_KEY'] = api_key
                logger.info(f"Set CARTESIA_API_KEY environment variable with length {len(api_key)}")
            else:  # openai
                os.environ['OPENAI_API_KEY'] = api_key
                logger.info(f"Set OPENAI_API_KEY environment variable with length {len(api_key)}")
        
        logger.info(f"Synthesizing segment {segment_id} with {model} TTS using voice {voice_name}")
        
        # Synthesize speech with appropriate TTS engine
        if model.lower() == 'sarvam':
            # For Sarvam, we can directly use the voice name
            success = sarvam_synthesize(
                text=text,
                language=language,
                output_path=output_path,
                speaker=voice_name,
                pitch=0,
                pace=1.0,  # Default pace, will be adjusted in time alignment
                loudness=1.0
            )
        elif model.lower() == 'cartesia':
            # For Cartesia, we need to look up the voice ID from the voice name
            from modules.cartesia_tts import AVAILABLE_VOICES
            
            # Check if the voice name is directly a voice ID
            if voice_name in AVAILABLE_VOICES:
                # It's a voice name, get the ID
                voice_id = AVAILABLE_VOICES[voice_name]['id']
                logger.info(f"Using voice ID {voice_id} for voice name {voice_name}")
            else:
                # It might already be a voice ID or an unknown voice name
                voice_id = voice_name
                logger.warning(f"Voice name {voice_name} not found in Cartesia voices, using as-is")
            
            success = cartesia_synthesize(
                text=text,
                output_path=output_path,
                voice_id=voice_id
            )
        else:  # openai
            # For OpenAI, we use the character name from MCMOpenAIVoices.json
            # The mapping to OpenAI voices is handled in the openai_tts module
            success = openai_synthesize(
                text=text,
                voice_id=voice_name,
                output_path=output_path,
                api_key=api_key
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
        model: TTS model to use ('sarvam', 'cartesia', or 'openai')
        api_key: API key for the TTS service (optional)
        use_mock: Whether to use mock TTS instead of actual TTS service
        
    Returns:
        List: List of processed segments with synthesis information
    """
    processed_segments = []
    
    # Get all segments from merged data
    all_segments = merged_data.get('merged_segments', [])
    if not all_segments:
        logger.warning("No segments found in merged data")
        return processed_segments
    
    logger.info(f"Processing {len(all_segments)} segments with {model} TTS")
    
    # Process each segment
    for segment in all_segments:
        segment_id = segment.get('segment_id')
        speaker = segment.get('speaker', 'SPEAKER_00')
        text = segment.get('translated_text', '')
        
        if not text:
            logger.warning(f"No translated text found for segment {segment_id}, skipping")
            continue
        
        # Synthesize speech for this segment
        tts_file = synthesize_segment(
            segment,
            speaker_voice_map,
            paths['tts_dir'],
            model=model,
            api_key=api_key,
            use_mock=use_mock
        )
        
        if tts_file:
            # Add to processed segments
            processed_segments.append({
                'segment_id': segment_id,
                'speaker': speaker,
                'text': text,
                'tts_file': tts_file,
                'start_time': segment.get('start_time', 0),
                'end_time': segment.get('end_time', 0),
                'duration': segment.get('duration', 0),
                'status': 'success'  # Add status field to ensure segments are included in stitching
            })
    
    logger.info(f"Successfully processed {len(processed_segments)} segments")
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
    logger.info(f"Running time alignment for {len(processed_segments)} segments")
    
    # Create time alignment output directory
    time_aligned_dir = os.path.join(paths['test_output_dir'], 'time_aligned')
    os.makedirs(time_aligned_dir, exist_ok=True)
    
    # Initialize alignment metadata
    alignment_metadata = {
        'session_id': output_name,
        'aligned_segments': [],
        'segments': []  # Required for stitch_time_aligned_segments
    }
    
    # Load merged data
    with open(merged_data_path, 'r', encoding='utf-8') as f:
        merged_data = json.load(f)
    
    merged_segments = merged_data.get("merged_segments", [])
    merged_segments_map = {s.get("segment_id"): s for s in merged_segments}
    
    # Process each segment
    for segment_info in processed_segments:
        segment_id = segment_info.get("segment_id")
        input_path = segment_info.get("tts_file")
        
        if not input_path or not os.path.exists(input_path):
            logger.warning(f"No audio path found for segment {segment_id}, skipping time alignment")
            continue
        
        # Get target duration from merged data
        merged_segment = merged_segments_map.get(segment_id)
        if not merged_segment:
            logger.warning(f"No merged segment found for segment {segment_id}, skipping time alignment")
            continue
        
        target_duration = merged_segment.get("duration", 0)
        if target_duration <= 0:
            logger.warning(f"Invalid target duration for segment {segment_id}: {target_duration}, skipping")
            continue
        
        # Create output path for time-aligned segment
        output_path = os.path.join(time_aligned_dir, f"segment_{segment_id}_aligned.wav")
        
        try:
            # Get original duration of the TTS file
            with wave.open(input_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                original_duration = frames / float(rate)
            
            # Calculate speed factor
            if target_duration is None or target_duration <= 0:
                # If no target duration, use the original duration
                target_duration = original_duration
                speed_factor = 1.0
            else:
                # Calculate speed factor to match target duration
                speed_factor = original_duration / target_duration
            
            # Adjust speed to match target duration
            logger.info(f"Adjusting segment duration: original={original_duration:.2f}s, target={target_duration:.2f}s, speed_factor={speed_factor:.4f}")
            
            # Use time_aligned_tts module to adjust speed
            from modules.time_aligned_tts import adjust_segment_duration
            success, adjustment_info = adjust_segment_duration(
                input_path=input_path,
                output_path=output_path,
                target_duration=target_duration
            )
            adjusted_path = output_path if success else None
            
            if adjusted_path and os.path.exists(adjusted_path):
                # Verify the adjusted duration
                with wave.open(adjusted_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    adjusted_duration = frames / float(rate)
                
                logger.info(f"Output duration: {adjusted_duration:.2f}s (target: {target_duration:.2f}s, difference: {abs(adjusted_duration - target_duration):.2f}s)")
                
                # Add to alignment metadata - aligned_segments
                alignment_metadata['aligned_segments'].append({
                    'segment_id': segment_id,
                    'original_file': input_path,
                    'aligned_file': adjusted_path,
                    'start_time': merged_segment.get("start_time", 0),
                    'end_time': merged_segment.get("end_time", 0),
                    'original_duration': original_duration,
                    'target_duration': target_duration,
                    'adjusted_duration': adjusted_duration,
                    'speed_factor': speed_factor
                })
                
                # Also add to segments list in the format expected by stitch_time_aligned_segments
                alignment_metadata['segments'].append({
                    'segment_id': segment_id,
                    'start_time': merged_segment.get("start_time", 0),
                    'end_time': merged_segment.get("end_time", 0),
                    'aligned_file': adjusted_path,
                    'output_file': adjusted_path,  # Add output_file field to match what stitch_time_aligned_segments expects
                    'output_duration': adjusted_duration,  # Add output_duration to help with sequential placement
                    'speaker': segment_info.get("speaker", ""),
                    'status': 'success'  # Add status field to ensure segments are included in stitching
                })
                
                logger.info(f"Successfully time-aligned segment {segment_id}")
            else:
                logger.error(f"Failed to time-align segment {segment_id}")
        except Exception as e:
            logger.error(f"Error time-aligning segment {segment_id}: {e}")
    
    # Sort segments by start_time to ensure correct sequential placement during stitching
    alignment_metadata['segments'] = sorted(alignment_metadata['segments'], key=lambda x: x.get('start_time', 0))
    
    # Save alignment metadata
    metadata_path = os.path.join(paths['test_output_dir'], f"{output_name}_alignment_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(alignment_metadata, f, indent=2)
    
    logger.info(f"Time alignment completed, metadata saved to {metadata_path}")
    return alignment_metadata

def stitch_segments_sequential(
    output_name: str,
    alignment_metadata: Dict[str, Any],
    paths: Dict[str, str],
    original_audio_path: Optional[str] = None,
    background_music_path: Optional[str] = None,
    enable_background_music: bool = True
) -> str:
    """
    Custom function to stitch segments sequentially in the correct order.
    
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
    logger.info("Stitching segments sequentially in correct order")
    
    # Create output path for stitched audio
    stitched_output_path = os.path.join(paths['test_output_dir'], f"{output_name}_stitched.wav")
    
    # Check if we have any segments to stitch
    segments = alignment_metadata.get("segments", [])
    if not segments:
        logger.warning("No segments found in metadata, skipping stitching")
        return None
    
    # Sort segments by their start_time to ensure correct order
    segments = sorted(segments, key=lambda x: x.get('start_time', 0))
    
    try:
        # Import audio processing libraries
        from pydub import AudioSegment
        
        # Create an empty audio segment to start with
        final_audio = AudioSegment.silent(duration=0)
        
        # Process each segment in order
        for segment in segments:
            segment_id = segment.get('segment_id')
            audio_file = segment.get('aligned_file') or segment.get('output_file')
            status = segment.get('status')
            
            if status != 'success':
                logger.warning(f"Skipping segment {segment_id} with status {status}")
                continue
                
            if not audio_file or not os.path.exists(audio_file):
                logger.warning(f"Audio file not found for segment {segment_id}: {audio_file}")
                continue
                
            # Load segment audio
            try:
                segment_audio = AudioSegment.from_file(audio_file)
                # Append to the final audio (true sequential placement)
                final_audio += segment_audio
                logger.info(f"Added segment {segment_id} (duration: {len(segment_audio)/1000:.2f}s)")
            except Exception as e:
                logger.error(f"Error processing segment {segment_id}: {str(e)}")
        
        # Add background music if enabled and provided
        if enable_background_music and background_music_path and os.path.exists(background_music_path):
            try:
                logger.info(f"Adding background music from {background_music_path}")
                background_music = AudioSegment.from_file(background_music_path)
                
                # Loop the background music if it's shorter than the speech
                final_duration_ms = len(final_audio)
                background_duration_ms = len(background_music)
                
                if background_duration_ms < final_duration_ms:
                    # Calculate how many times we need to loop the background music
                    loops_needed = int(final_duration_ms / background_duration_ms) + 1
                    looped_background = background_music * loops_needed
                    # Trim to match final audio length
                    background_music = looped_background[:final_duration_ms]
                else:
                    # Trim background music to match final audio length
                    background_music = background_music[:final_duration_ms]
                
                # Lower the volume of the background music (to -20dB)
                background_music = background_music - 20  # Reduce volume by 20dB
                
                # Overlay the background music with the speech
                final_audio = final_audio.overlay(background_music)
                logger.info(f"Background music added (duration: {len(background_music)/1000:.2f}s)")
            except Exception as e:
                logger.error(f"Error adding background music: {str(e)}")
        else:
            if not enable_background_music:
                logger.info("Background music disabled by user preference")
            elif not background_music_path:
                logger.info("No background music path provided")
            elif not os.path.exists(background_music_path):
                logger.warning(f"Background music file not found: {background_music_path}")
        
        # Export the final stitched audio
        final_audio.export(stitched_output_path, format="wav")
        logger.info(f"Time-aligned audio saved to {stitched_output_path} (duration: {len(final_audio)/1000:.2f}s)")
        return stitched_output_path
        
    except Exception as e:
        logger.error(f"Error stitching segments: {e}")
        import traceback

def add_background_music(audio_file: str, background_music_path: str, volume: float = 0.1) -> str:
    """
    Add background music to an audio file.
    
    Args:
        audio_file: Path to the audio file
        background_music_path: Path to the background music file
        volume: Volume of the background music (0.0 to 1.0)
        
    Returns:
        str: Path to the output file with background music
    """
    if not os.path.exists(background_music_path):
        logger.warning(f"Background music file not found: {background_music_path}")
        return audio_file
        
    try:
        # Load the audio file and background music
        audio = AudioSegment.from_wav(audio_file)
        background = AudioSegment.from_wav(background_music_path)
        
        # Adjust background volume
        background = background - (20 * (1 - volume))  # Reduce volume
        
        # Loop background if needed
        if len(background) < len(audio):
            loops_needed = math.ceil(len(audio) / len(background))
            background = background * loops_needed
        
        # Trim background to match audio length
        background = background[:len(audio)]
        
        # Overlay background onto audio
        output = audio.overlay(background, position=0)
        
        # Save output file
        output_file = audio_file.replace('.wav', '_with_music.wav')
        output.export(output_file, format="wav")
        
        logger.info(f"Added background music to {audio_file}, saved as {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error adding background music: {str(e)}")
        return audio_file

def stitch_segments(output_name: str, alignment_metadata: Dict, paths: Dict, merged_file: str, original_audio_path: Optional[str] = None, background_music_path: Optional[str] = None) -> str:
    """
    Stitch segments together using the time-aligned TTS function.
    
    Args:
        output_name: Name for the output directory or session ID
        alignment_metadata: Metadata from time alignment
        paths: Dictionary of paths
        merged_file: Path to merged file
        original_audio_path: Path to original audio file
        background_music_path: Path to background music file
        
    Returns:
        str: Path to final output file
    """
    from modules.time_aligned_tts import stitch_time_aligned_segments
    
    # Check if we're using an existing session directory
    is_existing_session = 'outputs' in paths['test_output_dir']
    
    if is_existing_session:
        # For existing sessions, we don't need to create additional directories
        # or copy files as they should already be in the right place
        logger.info(f"Using existing session structure at {paths['test_output_dir']}")
        
        # Create a merged diarization file with the segments from alignment_metadata
        merged_data = {"merged_segments": []}
        for segment in alignment_metadata.get("segments", []):
            merged_data["merged_segments"].append({
                "segment_id": segment.get("segment_id", ""),
                "start_time": segment.get("start_time", 0),
                "end_time": segment.get("end_time", 0),
                "speaker": segment.get("speaker", "")
            })
        
        logger.info(f"Created merged diarization file with {len(merged_data['merged_segments'])} segments")
    else:
        # For new test runs, create the directory structure and copy files
        # Create merged diarization file in the expected location
        merged_dir = os.path.join(paths['test_output_dir'], output_name)
        os.makedirs(merged_dir, exist_ok=True)
        
        # Create subdirectories
        merged_audio_dir = os.path.join(merged_dir, 'audio')
        os.makedirs(merged_audio_dir, exist_ok=True)
        
        # Copy merged file to expected location
        merged_file_copy = os.path.join(merged_dir, 'diarization_translated_merged.json')
        shutil.copy2(merged_file, merged_file_copy)
        
        # Copy original audio to expected location if provided
        if original_audio_path:
            original_audio_copy = os.path.join(merged_audio_dir, f'session_{output_name}.wav')
            shutil.copy2(original_audio_path, original_audio_copy)
            logger.info(f"Copied original audio to {original_audio_copy}")
            original_audio_path = original_audio_copy
    
    # Stitch time-aligned segments
    # For existing sessions, we need to handle the complex directory structure
    is_existing_session = 'outputs' in paths['test_output_dir']
    
    if is_existing_session:
        # For existing sessions, we need to handle potential nested session directories
        session_dir = paths['test_output_dir']
        session_id = output_name.replace('session_', '') if output_name.startswith('session_') else output_name
        
        # Check for timing files in both possible locations
        # First, check if there's a diarization_translated_merged.json directly in the session directory
        direct_merged_file = os.path.join(session_dir, 'diarization_translated_merged.json')
        nested_merged_file = os.path.join(session_dir, f"session_{session_id}", 'diarization_translated_merged.json')
        nested_merged_file2 = os.path.join(session_dir, session_id, 'diarization_translated_merged.json')
        
        # Log which files exist to help with debugging
        logger.info(f"Checking for timing files in multiple locations:")
        logger.info(f"  - Direct merged file: {direct_merged_file} (exists: {os.path.exists(direct_merged_file)})")
        logger.info(f"  - Nested merged file: {nested_merged_file} (exists: {os.path.exists(nested_merged_file)})")
        logger.info(f"  - Nested merged file 2: {nested_merged_file2} (exists: {os.path.exists(nested_merged_file2)})")
        
        # Determine the correct output_dir to use based on where the timing files are found
        if os.path.exists(direct_merged_file):
            # If the file exists directly in the session directory, use the parent directory
            output_dir = os.path.dirname(session_dir)
            logger.info(f"Using direct path structure with output_dir: {output_dir}")
        elif os.path.exists(nested_merged_file):
            # If the file exists in a nested session directory, use the session directory as output_dir
            output_dir = session_dir
            logger.info(f"Using nested path structure with output_dir: {output_dir}")
        elif os.path.exists(nested_merged_file2):
            # If the file exists in a nested session directory without 'session_' prefix
            output_dir = session_dir
            logger.info(f"Using nested path structure (without session_ prefix) with output_dir: {output_dir}")
        else:
            # If no timing files are found, default to the parent directory
            output_dir = os.path.dirname(session_dir)
            logger.warning(f"No timing files found in any expected location. Using default output_dir: {output_dir}")
    else:
        # For new test runs, use the test_output_dir as is
        output_dir = paths['test_output_dir']
        session_id = output_name
    
    # Define a custom output file path to avoid path issues
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    custom_output_file = os.path.join(paths['test_output_dir'], f"final_output_time_aligned_{timestamp}.wav")
    
    # Load timing metadata directly from the diarization_translated_merged.json file
    timing_metadata = None
    metadata_file = None
    
    # Try to load timing metadata from the diarization_translated_merged.json file
    if is_existing_session:
        # Check both possible locations for the diarization_translated_merged.json file
        possible_timing_files = [
            os.path.join(session_dir, 'diarization_translated_merged.json'),
            os.path.join(session_dir, f"session_{session_id}", 'diarization_translated_merged.json'),
            os.path.join(session_dir, session_id, 'diarization_translated_merged.json')
        ]
        
        # Try each possible location
        for timing_file in possible_timing_files:
            if os.path.exists(timing_file):
                logger.info(f"Loading timing metadata from: {timing_file}")
                try:
                    with open(timing_file, 'r') as f:
                        timing_data = json.load(f)
                        if 'merged_segments' in timing_data:
                            # Create a map of segment IDs to timing segments
                            # Map "merged_000" to the actual segment ID in the timing data
                            timing_metadata = {}
                            timing_metadata['merged_segments'] = timing_data['merged_segments']
                            
                            # Log the segment IDs found in the timing data
                            segment_ids = [seg.get('segment_id', 'unknown') for seg in timing_data['merged_segments']]
                            logger.info(f"Found timing segments with IDs: {segment_ids}")
                            
                            # The timing data already has the correct segment IDs, we just need to ensure we use them correctly
                            # Create a direct mapping for the alignment_metadata
                            alignment_metadata = {}
                            alignment_metadata['segments'] = []
                            
                            # We need to preserve the exact timing data structure expected by stitch_time_aligned_segments
                            # The function expects a list of segments with start and end times in milliseconds
                            
                            # Create a mapping of original segment IDs to their timing data
                            timing_map = {seg.get('segment_id', f"unknown_{i}"): seg for i, seg in enumerate(timing_data['merged_segments'])}
                            
                            # Log the timing map keys to help with debugging
                            logger.info(f"Timing map keys: {list(timing_map.keys())}")
                            
                            # Create a new timing_segments list that will be passed directly to the stitch function
                            timing_segments = []
                            
                            # Map the segment IDs from the timing data to the segment IDs used in the script
                            for i in range(len(timing_data['merged_segments'])):
                                segment_id = f"merged_{i:03d}"
                                
                                # Check if this segment_id exists in the timing map
                                if segment_id in timing_map:
                                    # Use the timing data directly
                                    new_seg = dict(timing_map[segment_id])
                                    logger.info(f"Using direct timing data for {segment_id}")
                                else:
                                    # Create a new segment with timing from the corresponding index
                                    new_seg = dict(timing_data['merged_segments'][i])
                                    logger.info(f"Using indexed timing data for {segment_id}")
                                
                                # Ensure the segment_id is correct
                                new_seg['segment_id'] = segment_id
                                
                                # Add to the timing_segments list that will be passed to stitch_time_aligned_segments
                                timing_segments.append(new_seg)
                                # Add status and output_file fields required by stitch_time_aligned_segments
                                new_seg['status'] = "success"
                                
                                # Find the corresponding output file for this segment
                                # Try with the 'segment_' prefix first, which is the correct format
                                segment_output_file = os.path.join(session_dir, 'synthesis', f"segment_merged_{i:03d}.wav")
                                
                                # Check for time-aligned version first
                                time_aligned_file = os.path.join(session_dir, 'synthesis', f"segment_merged_{i:03d}_time_aligned.wav")
                                
                                if os.path.exists(time_aligned_file):
                                    # Prefer time-aligned version if it exists
                                    new_seg['output_file'] = time_aligned_file
                                    logger.info(f"Using time-aligned file for segment merged_{i:03d}: {time_aligned_file}")
                                elif os.path.exists(segment_output_file):
                                    # Use regular segment file if time-aligned doesn't exist
                                    new_seg['output_file'] = segment_output_file
                                    logger.info(f"Using segment file for merged_{i:03d}: {segment_output_file}")
                                else:
                                    # Try alternative locations and naming patterns
                                    possible_files = [
                                        # Try with segment_ prefix in different locations
                                        os.path.join(session_dir, f"session_{session_id}", 'synthesis', f"segment_merged_{i:03d}.wav"),
                                        os.path.join(session_dir, session_id, 'synthesis', f"segment_merged_{i:03d}.wav"),
                                        # Try without segment_ prefix
                                        os.path.join(session_dir, 'synthesis', f"merged_{i:03d}.wav"),
                                        os.path.join(session_dir, f"session_{session_id}", 'synthesis', f"merged_{i:03d}.wav"),
                                        os.path.join(session_dir, session_id, 'synthesis', f"merged_{i:03d}.wav"),
                                        # Try with time_aligned suffix
                                        os.path.join(session_dir, f"session_{session_id}", 'synthesis', f"segment_merged_{i:03d}_time_aligned.wav"),
                                        os.path.join(session_dir, session_id, 'synthesis', f"segment_merged_{i:03d}_time_aligned.wav"),
                                    ]
                                    
                                    found_file = False
                                    for file_path in possible_files:
                                        if os.path.exists(file_path):
                                            new_seg['output_file'] = file_path
                                            logger.info(f"Found alternative file for segment merged_{i:03d}: {file_path}")
                                            found_file = True
                                            break
                                    
                                    if not found_file:
                                        logger.warning(f"Could not find output file for segment merged_{i:03d}")
                                        new_seg['status'] = "error"
                                        new_seg['output_file'] = None
                                
                                alignment_metadata['segments'].append(new_seg)
                            
                            logger.info(f"Created alignment metadata with {len(alignment_metadata['segments'])} segments")
                            
                            # The core function expects timing_segments to have the same segment_id format as our alignment_metadata
                            # We need to ensure the timing data is correctly structured for the stitch_time_aligned_segments function
                            
                            # First, extract the timing information from the original timing data
                            original_timing = {}
                            for seg in timing_data['merged_segments']:
                                segment_id = seg.get('segment_id', '')
                                if segment_id:
                                    # Store the original timing information
                                    original_timing[segment_id] = {
                                        'start_time': seg.get('start_time', 0),
                                        'end_time': seg.get('end_time', 0),
                                        'duration': seg.get('duration', 0)
                                    }
                            
                            # Now create a new timing_segments list with the exact structure expected by stitch_time_aligned_segments
                            # This is the key fix - we need to ensure segment_id in timing_segments matches segment_id in alignment_metadata
                            timing_segments = []
                            for seg in alignment_metadata['segments']:
                                segment_id = seg.get('segment_id', '')
                                if segment_id in original_timing:
                                    # Create a new timing segment with the original timing info but the correct segment_id
                                    # IMPORTANT: Keep timing data in seconds as expected by the core function
                                    # The core function will convert seconds to milliseconds internally
                                    start_time_sec = original_timing[segment_id]['start_time']
                                    end_time_sec = original_timing[segment_id]['end_time']
                                    duration_sec = end_time_sec - start_time_sec
                                    
                                    timing_segment = {
                                        'segment_id': segment_id,  # This must match exactly
                                        'start_time': start_time_sec,  # Keep in seconds
                                        'end_time': end_time_sec,      # Keep in seconds
                                        'duration': duration_sec,       # Keep in seconds
                                        'speaker': original_timing[segment_id].get('speaker', 'UNKNOWN'),
                                        'text': original_timing[segment_id].get('text', ''),
                                        'translated_text': original_timing[segment_id].get('translated_text', '')
                                    }
                                    timing_segments.append(timing_segment)
                                    logger.info(f"Created timing segment for {segment_id} with start_time={start_time_sec}s, end_time={end_time_sec}s, duration={duration_sec}s")
                            # First, let's inspect the structure of the alignment_metadata
                            logger.info(f"Original alignment_metadata keys: {list(alignment_metadata.keys())}")
                            
                            # Create enhanced metadata with timing segments directly included
                            enhanced_metadata = alignment_metadata.copy()  # Start with a copy of the original
                            enhanced_metadata['timing_segments'] = timing_segments  # Add timing_segments directly
                            
                            # Also add timing_segments directly to the root level for compatibility
                            # This ensures the core function can find them regardless of how it's looking for them
                            timing_segments_dict = {seg['segment_id']: seg for seg in timing_segments}
                            logger.info(f"Created timing_segments_dict with keys: {list(timing_segments_dict.keys())}")
                            
                            # Save our timing segments to a debug file
                            timing_debug_path = os.path.join(session_dir, 'debug_timing_data.json')
                            with open(timing_debug_path, 'w') as f:
                                json.dump({'segments': timing_segments}, f, indent=2)
                            logger.info(f"Saved debug timing data to {timing_debug_path} with {len(timing_segments)} segments")
                            
                            # Log what we're passing to the core function
                            logger.info(f"Passing {len(timing_segments)} timing segments directly in the alignment_metadata dictionary")
                            for seg in timing_segments:
                                logger.info(f"  - {seg['segment_id']}: start={seg['start_time']}s, end={seg['end_time']}s")
                            
                            # Create a custom output file path
                            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            custom_output_file = os.path.join(session_dir, f"final_output_time_aligned_{timestamp}.wav")
                            
                            # Import the core function and any other needed modules
                            import sys
                            from modules.time_aligned_tts import stitch_time_aligned_segments
                            
                            # Direct approach - modify the core function to use our timing segments
                            import modules.time_aligned_tts
                            import types
                            import inspect
                            import functools
                            
                            # Store our timing segments in a module-level dictionary for easy access
                            timing_segments_dict = {seg['segment_id']: seg for seg in timing_segments}
                            logger.info(f"Created timing_segments_dict with keys: {list(timing_segments_dict.keys())}")
                            
                            # Store the original stitch_time_aligned_segments function
                            original_stitch_function = modules.time_aligned_tts.stitch_time_aligned_segments
                            
                            # Analyze the source code of the original function to find the timing segment lookup
                            source = inspect.getsource(original_stitch_function)
                            logger.info(f"Found source code for stitch_time_aligned_segments, length: {len(source)} characters")
                            
                            # Create a more direct approach using AudioSegment patching
                            from pydub import AudioSegment
                            import inspect
                            
                            # Log what we're about to do
                            logger.info(f"Enhanced metadata keys: {list(enhanced_metadata.keys())}")
                            logger.info(f"Enhanced metadata contains {len(timing_segments)} timing segments")
                            
                            # Store the original AudioSegment.from_file method
                            original_from_file = AudioSegment.from_file
                            
                            # Create a patched version of AudioSegment.from_file that will inject our timing segments
                            def patched_from_file(file, format=None, **kwargs):
                                # Call the original method to get the audio segment
                                segment = original_from_file(file, format, **kwargs)
                                
                                # Get the calling frame to access local variables in stitch_time_aligned_segments
                                frame = inspect.currentframe().f_back
                                
                                # Check if this is being called from stitch_time_aligned_segments
                                if frame and 'timing_segment_map' in frame.f_locals:
                                    # Replace the timing_segment_map with our custom one
                                    logger.info(f"Injecting custom timing_segment_map with {len(timing_segments_dict)} segments")
                                    frame.f_locals['timing_segment_map'] = timing_segments_dict
                                    
                                    # Log the segment IDs we're injecting
                                    logger.info(f"Injected timing segments with IDs: {list(timing_segments_dict.keys())}")
                                    
                                    # Force update of locals
                                    frame.f_locals.update(frame.f_locals)
                                
                                return segment
                            
                            try:
                                # Apply our patch - replace AudioSegment.from_file with our patched version
                                AudioSegment.from_file = patched_from_file
                                
                                # Call the stitch function with our enhanced metadata
                                logger.info(f"Calling stitch_time_aligned_segments with enhanced metadata containing timing segments")
                                output_file = stitch_time_aligned_segments(
                                    session_id=session_id,
                                    output_dir=output_dir,
                                    alignment_metadata=enhanced_metadata,
                                    output_file=custom_output_file,
                                    original_audio_path=original_audio_path
                                )
                                
                                logger.info(f"Stitching completed, output saved to: {output_file}")
                                final_output_file = output_file
                            finally:
                                # Restore the original from_file method
                                AudioSegment.from_file = original_from_file
                                logger.info("Restored original stitch_time_aligned_segments function")
                            
                            # Make sure we have a valid output file before proceeding
                            if final_output_file and os.path.exists(final_output_file):
                                # If background music was provided, add it to the output
                                if background_music_path and os.path.exists(background_music_path):
                                    logger.info(f"Adding background music from {background_music_path}")
                                    from pydub import AudioSegment
                                    
                                    # Load the output file and background music
                                    output_audio = AudioSegment.from_file(final_output_file)
                                    music = AudioSegment.from_file(background_music_path)
                                    
                                    # Ensure music is long enough (loop if needed)
                                    if len(music) < len(output_audio):
                                        repeats = math.ceil(len(output_audio) / len(music))
                                        music = music * repeats
                                    
                                    # Trim music to match output length
                                    music = music[:len(output_audio)]
                                    
                                    # Lower the volume of the music
                                    music = music - 12  # -12 dB
                                    
                                    # Mix the output with the background music
                                    mixed = output_audio.overlay(music)
                                    
                                    # Save the mixed output
                                    output_with_music = final_output_file.replace('.wav', '_with_music.wav')
                                    mixed.export(output_with_music, format="wav")
                                    logger.info(f"Added background music to {final_output_file}, saved as {output_with_music}")
                                    logger.info(f"Background music added, final output: {output_with_music}")
                                    final_output_file = output_with_music
                                
                                logger.info(f"Test completed successfully. Final output: {final_output_file}")
                                print("Test completed successfully!")
                                print(f"Final output: {final_output_file}")
                                return final_output_file
                            
                            logger.info(f"Test completed successfully. Final output: {output_file}")
                            print("Test completed successfully!")
                            print(f"Final output: {output_file}")
                            
                            # Call the core function with our enhanced metadata
                            logger.info(f"Calling stitch_time_aligned_segments with enhanced metadata containing timing segments")
                            
                            # Add a monkey patch to directly replace the timing_segment_map in the core function
                            def monkey_patch_map(original_func, timing_segments):
                                def wrapper(*args, **kwargs):
                                    # Call the original function
                                    result = original_func(*args, **kwargs)
                                    
                                    # Directly modify the timing_segment_map in the core module
                                    if hasattr(modules.time_aligned_tts, 'timing_segment_map'):
                                        # Create our own map with exact segment IDs
                                        our_map = {seg['segment_id']: seg for seg in timing_segments}
                                        logger.info(f"Directly replacing timing_segment_map with our map containing keys: {list(our_map.keys())}")
                                        modules.time_aligned_tts.timing_segment_map = our_map
                                    
                                    return result
                                return wrapper
                            
                            # Apply the monkey patch
                            # modules.time_aligned_tts.stitch_time_aligned_segments = monkey_patch_map(modules.time_aligned_tts.stitch_time_aligned_segments, timing_segments)
                            
                            # Call the core function with our enhanced metadata
                            output_file = stitch_time_aligned_segments(
                                session_id=session_id,
                                output_dir=output_dir,
                                alignment_metadata=enhanced_metadata,  # Use our enhanced metadata with timing_segments
                                output_file=custom_output_file,
                                original_audio_path=original_audio_path
                            )
                            
                            logger.info(f"Stitching completed, output saved to: {output_file}")
                            
                            # Restore the original stitch_time_aligned_segments function
                            modules.time_aligned_tts.stitch_time_aligned_segments = original_stitch_function
                            logger.info("Restored original stitch_time_aligned_segments function")
                            
                            # Add background music if provided
                            if background_music_path:
                                logger.info(f"Adding background music from {background_music_path}")
                                output_file = add_background_music(output_file, background_music_path)
                                logger.info(f"Background music added, final output: {output_file}")
                            
                            return output_file
                            
                except Exception as e:
                    logger.error(f"Error loading timing metadata from {timing_file}: {str(e)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Also check for the time_alignment_metadata.json file as a fallback
        if not timing_metadata:
            direct_metadata = os.path.join(session_dir, 'synthesis', 'time_alignment_metadata.json')
            nested_metadata = os.path.join(session_dir, f"session_{session_id}", 'synthesis', 'time_alignment_metadata.json')
            nested_metadata2 = os.path.join(session_dir, session_id, 'synthesis', 'time_alignment_metadata.json')
            
            for meta_file in [direct_metadata, nested_metadata, nested_metadata2]:
                if os.path.exists(meta_file):
                    metadata_file = meta_file
                    logger.info(f"Using metadata file as fallback: {metadata_file}")
                    break
    
    # If we couldn't find any timing metadata, fall back to the original method
    logger.warning("No timing metadata found, falling back to sequential stitching")
    
    # Create a fallback output file path
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    fallback_output_file = os.path.join(session_dir, f"final_output_sequential_{timestamp}.wav")
    
    # Call the core function with basic parameters
    logger.info(f"Using fallback sequential stitching to {fallback_output_file}")
    output_file = stitch_time_aligned_segments(
        session_id=session_id,
        output_dir=output_dir,
        alignment_metadata=alignment_metadata,
        output_file=fallback_output_file,
        original_audio_path=original_audio_path
    )
    
    # Add background music if provided
    if background_music_path and output_file:
        logger.info(f"Adding background music from {background_music_path}")
        output_file = add_background_music(output_file, background_music_path)
        logger.info(f"Background music added, final output: {output_file}")
    
    return output_file

def main():
    """Main function to run the test."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test Time-Aligned TTS with multiple providers')
    # Create a mutually exclusive group for session_id or merged_file
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--session_id', help='Use an existing session ID instead of creating a new test')
    source_group.add_argument('--merged_file', help='Path to diarization_translated_merged.json file')
    
    parser.add_argument('--model', choices=['sarvam', 'cartesia', 'openai'], default='sarvam', 
                        help='TTS model to use (sarvam, cartesia, or openai)')
    parser.add_argument('--original_audio', help='Path to original audio file (optional)')
    parser.add_argument('--background_music', help='Path to background music file (optional)')
    parser.add_argument('--disable_background_music', action='store_true', help='Disable background music even if provided')
    parser.add_argument('--output_name', help='Name for output directory (defaults to timestamp)')
    parser.add_argument('--speaker_0', help='Voice name for SPEAKER_00')
    parser.add_argument('--speaker_1', help='Voice name for SPEAKER_01')
    parser.add_argument('--speaker_2', help='Voice name for SPEAKER_02')
    parser.add_argument('--speaker_3', help='Voice name for SPEAKER_03')
    parser.add_argument('--default', help='Default voice name for unknown speakers')
    parser.add_argument('--api_key', help='API key for the selected TTS service')
    parser.add_argument('--use_mock', action='store_true', help='Use mock TTS instead of actual TTS service')
    
    args = parser.parse_args()
    
    # Set default voice names based on the selected model
    if args.model.lower() == 'sarvam':
        # Sarvam uses lowercase voice names
        speaker_0_default = 'anushka'
        speaker_1_default = 'abhilash'
        speaker_2_default = 'karun'
        speaker_3_default = 'vidya'
        default_default = 'manisha'
    elif args.model.lower() == 'cartesia':
        # Cartesia uses proper case voice names that match the keys in AVAILABLE_VOICES
        speaker_0_default = 'Vaishnavi'
        speaker_1_default = 'Sandilya'
        speaker_2_default = 'Madhu'
        speaker_3_default = 'Budatha'
        default_default = 'Mahesh'
    else:  # openai
        # OpenAI uses character names from MCMOpenAIVoices.json
        speaker_0_default = 'Madhu'
        speaker_1_default = 'Mahesh'
        speaker_2_default = 'Mother'
        speaker_3_default = 'Bobby'
        default_default = 'Madhu'
    
    # Create speaker-voice mapping with defaults if not provided
    speaker_voice_map = {
        'SPEAKER_00': args.speaker_0 if args.speaker_0 else speaker_0_default,
        'SPEAKER_01': args.speaker_1 if args.speaker_1 else speaker_1_default,
        'SPEAKER_02': args.speaker_2 if args.speaker_2 else speaker_2_default,
        'SPEAKER_03': args.speaker_3 if args.speaker_3 else speaker_3_default,
        'default': args.default if args.default else default_default
    }
    
    # Determine if we're using an existing session or creating a new test
    is_existing_session = args.session_id is not None
    
    if is_existing_session:
        # Use the provided session ID
        output_name = args.session_id
        logger.info(f"Using existing session: {output_name}")
        
        # Set up directories based on existing session
        try:
            paths = setup_test_directories(output_name, is_existing_session=True)
        except FileNotFoundError as e:
            logger.error(f"Error: {str(e)}")
            print(f"\nError: {str(e)}")
            return
        
        # Find the merged file in the existing session directory
        merged_file_path = os.path.join(paths['test_output_dir'], 'diarization_translated_merged.json')
        if not os.path.exists(merged_file_path):
            logger.error(f"Merged file not found in session directory: {merged_file_path}")
            print(f"\nError: Merged file not found in session directory: {merged_file_path}")
            return
        
        # Load merged segments from the existing file
        merged_data = load_merged_segments(merged_file_path)
        merged_file_copy = merged_file_path  # No need to copy, use the existing file
        
        # Find the original audio file in the existing session directory
        # Try to find any .wav file in the audio directory
        audio_files = [f for f in os.listdir(paths['audio_dir']) if f.endswith('.wav')]
        original_audio_path = None
        if audio_files:
            original_audio_path = os.path.join(paths['audio_dir'], audio_files[0])
            logger.info(f"Found original audio file: {original_audio_path}")
        else:
            logger.warning(f"No audio files found in: {paths['audio_dir']}")
    else:
        # Generate output name if not provided (for new test runs)
        output_name = args.output_name
        if not output_name:
            output_name = f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create test output directory
        os.makedirs('test_outputs', exist_ok=True)
        
        # Set up test directories for a new test run
        paths = setup_test_directories(output_name)
        
        # Load merged segments from the provided file
        if not os.path.exists(args.merged_file):
            logger.error(f"Merged segments file not found: {args.merged_file}")
            print(f"\nError: Merged segments file not found: {args.merged_file}")
            return
        
        merged_data = load_merged_segments(args.merged_file)
        
        # Copy the merged file to the test output directory for reference
        merged_file_copy = os.path.join(paths['test_output_dir'], 'diarization_translated_merged.json')
        shutil.copy2(args.merged_file, merged_file_copy)
        
        # Copy original audio if provided
        original_audio_path = None
        if args.original_audio and os.path.exists(args.original_audio):
            original_audio_copy = os.path.join(paths['audio_dir'], os.path.basename(args.original_audio))
            shutil.copy2(args.original_audio, original_audio_copy)
            original_audio_path = original_audio_copy
            logger.info(f"Copied original audio to {original_audio_copy}")
    
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
    
    # Stitch segments
    logger.info("Stitching segments")
    final_output_path = stitch_segments(
        output_name, 
        alignment_metadata, 
        paths, 
        merged_file_copy,  # Pass the merged file to stitch_segments
        original_audio_path,
        args.background_music
    )
    
    if final_output_path:
        logger.info(f"Test completed successfully. Final output: {final_output_path}")
        print(f"\nTest completed successfully!\nFinal output: {final_output_path}")
    else:
        logger.error("Test failed")
        print("\nTest failed. Check logs for details.")

if __name__ == "__main__":
    main()
