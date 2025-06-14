#!/usr/bin/env python3
"""
Voice Activity Detection (VAD) module for audio segmentation.
Uses Silero VAD to detect speech segments in audio files.
"""

import os
import json
import logging
import torch
import numpy as np
import librosa
import soundfile as sf
from typing import List, Tuple, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Default VAD Configuration
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_VAD_THRESHOLD = 0.5
DEFAULT_COMBINE_DURATION = 8  # Maximum duration for combined segments in seconds
DEFAULT_COMBINE_GAP = 1  # Maximum gap between segments to combine in seconds

@torch.no_grad()
def get_vad_probs(model: torch.nn.Module, audio: np.ndarray, sample_rate: int = 16000) -> List[float]:
    """
    Get speech probability for each audio window using Silero VAD.
    
    Args:
        model: Silero VAD model
        audio: Audio data as numpy array
        sample_rate: Audio sample rate
        
    Returns:
        List of speech probabilities for each window
    """
    audio = torch.as_tensor(audio, dtype=torch.float32)
    window_size_samples = 512 if sample_rate == 16000 else 256

    model.reset_states()
    audio_length_samples = len(audio)

    speech_probs = []
    for current_start_sample in range(0, audio_length_samples, window_size_samples):
        chunk = audio[current_start_sample: current_start_sample + window_size_samples]
        if len(chunk) < window_size_samples:
            chunk = torch.nn.functional.pad(chunk, (0, int(window_size_samples - len(chunk))))
        speech_prob = model(chunk, sample_rate).item()
        speech_probs.append(speech_prob)

    return speech_probs

def get_utterances(vad_probs: List[float], threshold: float = 0.5, frame_duration: float = 0.032) -> List[Tuple[float, float]]:
    """
    Extract utterances (start and end times) based on VAD probabilities.
    
    Args:
        vad_probs: List of speech probabilities
        threshold: Threshold for speech detection
        frame_duration: Duration of each frame in seconds
        
    Returns:
        List of tuples containing (start_time, end_time) for each utterance
    """
    utterances = []
    in_utterance = False
    utterance_start = 0

    for i, prob in enumerate(vad_probs):
        if prob > threshold and not in_utterance:
            in_utterance = True
            utterance_start = i * frame_duration
        elif prob <= threshold and in_utterance:
            in_utterance = False
            utterance_end = i * frame_duration
            if utterance_end - utterance_start > 0:
                utterances.append((utterance_start, utterance_end))

    if in_utterance:
        utterances.append((utterance_start, len(vad_probs) * frame_duration))

    return utterances

def merge_segments(segments: List[Tuple[float, float]], max_duration: float = 8, max_gap: float = 1) -> List[Tuple[float, float]]:
    """
    Combine segments with pauses shorter than max_gap seconds, with total duration limit.
    
    Args:
        segments: List of (start_time, end_time) tuples
        max_duration: Maximum duration for a combined segment
        max_gap: Maximum gap between segments to combine
        
    Returns:
        List of merged (start_time, end_time) tuples
    """
    merged_segments = []
    if not segments:
        return merged_segments  # Return empty if no segments are found

    current_start, current_end = segments[0]

    for start, end in segments[1:]:
        combined_duration = (end - current_start)

        if (start - current_end <= max_gap) and (combined_duration <= max_duration):
            current_end = end
        else:
            merged_segments.append((current_start, current_end))
            current_start, current_end = start, end

    merged_segments.append((current_start, current_end))
    return merged_segments

def load_vad_model() -> torch.nn.Module:
    """
    Load the Silero VAD model.
    
    Returns:
        Loaded VAD model
    """
    logger.info("Loading Silero VAD model...")
    try:
        vad_model, _ = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        vad_model.eval()
        logger.info("Silero VAD model loaded successfully")
        return vad_model
    except Exception as e:
        logger.error(f"Error loading VAD model: {e}")
        raise

def segment_audio_with_vad(
    audio_path: str, 
    output_dir: str = "vad_segments",
    min_segment_duration: float = 1.0,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    vad_threshold: float = DEFAULT_VAD_THRESHOLD,
    combine_duration: float = DEFAULT_COMBINE_DURATION,
    combine_gap: float = DEFAULT_COMBINE_GAP
) -> List[Dict[str, Any]]:
    """
    Segment audio file using VAD and save segments to files.
    
    Args:
        audio_path: Path to the audio file
        output_dir: Directory to save segmented audio files
        min_segment_duration: Minimum duration for segments in seconds
        sample_rate: Sample rate for audio processing
        vad_threshold: Threshold for speech detection
        combine_duration: Maximum duration for combined segments
        combine_gap: Maximum gap between segments to combine
        
    Returns:
        List of dictionaries containing segment information
    """
    logger.info(f"Segmenting audio with VAD: {audio_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load VAD model
    vad_model = load_vad_model()
    
    # Load audio file
    try:
        logger.info(f"Loading audio file: {audio_path}")
        audio_data, sr = librosa.load(audio_path, sr=sample_rate)
        logger.info(f"Audio loaded: {len(audio_data)/sample_rate:.2f} seconds at {sample_rate}Hz")
    except Exception as e:
        logger.error(f"Error loading audio file: {e}")
        return []
    
    # Get VAD probabilities
    logger.info("Detecting speech probabilities...")
    speech_probs = get_vad_probs(vad_model, audio_data, sample_rate)
    
    # Get utterances
    logger.info(f"Extracting utterances with threshold {vad_threshold}...")
    utterances = get_utterances(speech_probs, threshold=vad_threshold)
    
    if not utterances:
        logger.warning(f"No speech segments detected in {audio_path}")
        return []
    
    # Merge segments
    logger.info(f"Merging segments (max duration: {combine_duration}s, max gap: {combine_gap}s)...")
    merged_segments = merge_segments(utterances, max_duration=combine_duration, max_gap=combine_gap)
    
    # Filter segments by minimum duration
    if min_segment_duration > 0:
        logger.info(f"Filtering segments with minimum duration: {min_segment_duration}s")
        merged_segments = [(start, end) for start, end in merged_segments if (end - start) >= min_segment_duration]
        
    logger.info(f"Detected {len(merged_segments)} speech segments")
    
    # Extract and save each segment using librosa/soundfile
    segment_info = []
    for i, (start_time, end_time) in enumerate(merged_segments):
        # Convert to samples
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)
        
        # Extract segment
        segment_audio = audio_data[start_sample:end_sample]
        
        # Generate segment filename
        segment_filename = f"segment_{i:03d}.wav"
        segment_path = os.path.join(output_dir, segment_filename)
        
        # Save segment using soundfile
        try:
            sf.write(segment_path, segment_audio, sample_rate)
            
            # Add segment info
            segment_info.append({
                "segment_id": f"seg_{i:03d}",
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "file_path": segment_path
            })
            
            logger.info(f"Saved segment {i}: {start_time:.2f}s - {end_time:.2f}s ({end_time - start_time:.2f}s)")
        except Exception as e:
            logger.error(f"Error saving segment {i}: {e}")
    
    # Save segment info to JSON
    if segment_info:
        info_path = os.path.join(output_dir, "segment_info.json")
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(segment_info, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved segment info to: {info_path}")
    
    return segment_info

def segment_audio_without_saving(
    audio_path: str,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    vad_threshold: float = DEFAULT_VAD_THRESHOLD,
    combine_duration: float = DEFAULT_COMBINE_DURATION,
    combine_gap: float = DEFAULT_COMBINE_GAP
) -> List[Dict[str, Any]]:
    """
    Segment audio file using VAD without saving segments to disk.
    Useful for in-memory processing.
    
    Args:
        audio_path: Path to the audio file
        sample_rate: Sample rate for audio processing
        vad_threshold: Threshold for speech detection
        combine_duration: Maximum duration for combined segments
        combine_gap: Maximum gap between segments to combine
        
    Returns:
        List of dictionaries containing segment information and audio data
    """
    logger.info(f"Segmenting audio with VAD (in-memory): {audio_path}")
    
    # Load VAD model
    vad_model = load_vad_model()
    
    # Load audio file
    try:
        logger.info(f"Loading audio file: {audio_path}")
        audio_data, sr = librosa.load(audio_path, sr=sample_rate)
        logger.info(f"Audio loaded: {len(audio_data)/sample_rate:.2f} seconds at {sample_rate}Hz")
    except Exception as e:
        logger.error(f"Error loading audio file: {e}")
        return []
    
    # Get VAD probabilities
    logger.info("Detecting speech probabilities...")
    speech_probs = get_vad_probs(vad_model, audio_data, sample_rate)
    
    # Get utterances
    logger.info(f"Extracting utterances with threshold {vad_threshold}...")
    utterances = get_utterances(speech_probs, threshold=vad_threshold)
    
    if not utterances:
        logger.warning(f"No speech segments detected in {audio_path}")
        return []
    
    # Merge segments
    logger.info(f"Merging segments (max duration: {combine_duration}s, max gap: {combine_gap}s)...")
    merged_segments = merge_segments(utterances, max_duration=combine_duration, max_gap=combine_gap)
    
    logger.info(f"Detected {len(merged_segments)} speech segments")
    
    # Extract each segment
    segment_info = []
    for i, (start_time, end_time) in enumerate(merged_segments):
        # Convert to samples
        start_sample = int(start_time * sample_rate)
        end_sample = int(end_time * sample_rate)
        
        # Extract segment
        segment_audio = audio_data[start_sample:end_sample]
        
        # Add segment info
        segment_info.append({
            "segment_id": f"seg_{i:03d}",
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time,
            "audio_data": segment_audio,
            "sample_rate": sample_rate
        })
        
        logger.info(f"Extracted segment {i}: {start_time:.2f}s - {end_time:.2f}s ({end_time - start_time:.2f}s)")
    
    return segment_info
