#!/usr/bin/env python3
"""
Test script for VAD segmentation with Sarvam speech-to-text (without translation).
This script segments audio using VAD and processes each segment with Sarvam's STT API.
"""

import os
import json
import asyncio
import logging
import requests
import tempfile
import torch
import numpy as np
import librosa
import soundfile as sf
from io import BytesIO
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# VAD Configuration
SAMPLE_RATE = 16000
VAD_THRESHOLD = 0.5
COMBINE_DURATION = 8  # Maximum duration for combined segments in seconds
COMBINE_GAP = 1  # Maximum gap between segments to combine in seconds

@torch.no_grad()
def get_vad_probs(model, audio, sample_rate=16000):
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

def get_utterances(vad_probs, threshold=0.5, frame_duration=0.032):
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

def merge_segments(segments, max_duration=8, max_gap=1):
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

def segment_audio_with_vad(audio_path, output_dir="test_outputs/vad_segments"):
    """
    Segment audio file using VAD and save segments to files.
    
    Args:
        audio_path: Path to the audio file
        output_dir: Directory to save segmented audio files
        
    Returns:
        List of dictionaries containing segment information
    """
    logger.info(f"Segmenting audio with VAD: {audio_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load Silero VAD model
    vad_model, _ = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False,
        onnx=False
    )
    vad_model.eval()
    
    # Load audio file
    try:
        audio_data, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
    except Exception as e:
        logger.error(f"Error loading audio file: {e}")
        return []
    
    # Get VAD probabilities
    speech_probs = get_vad_probs(vad_model, audio_data, SAMPLE_RATE)
    
    # Get utterances
    utterances = get_utterances(speech_probs, threshold=VAD_THRESHOLD)
    
    if not utterances:
        logger.warning(f"No speech segments detected in {audio_path}")
        return []
    
    # Merge segments
    merged_segments = merge_segments(utterances, max_duration=COMBINE_DURATION, max_gap=COMBINE_GAP)
    
    logger.info(f"Detected {len(merged_segments)} speech segments")
    
    # Extract and save each segment using librosa/soundfile
    segment_info = []
    for i, (start_time, end_time) in enumerate(merged_segments):
        # Convert to samples
        start_sample = int(start_time * SAMPLE_RATE)
        end_sample = int(end_time * SAMPLE_RATE)
        
        # Extract segment
        segment_audio = audio_data[start_sample:end_sample]
        
        # Generate segment filename
        segment_filename = f"segment_{i+1:03d}.wav"
        segment_path = os.path.join(output_dir, segment_filename)
        
        # Save segment using soundfile
        try:
            sf.write(segment_path, segment_audio, SAMPLE_RATE)
            
            # Add segment info
            segment_info.append({
                "segment_id": f"seg_{i+1:03d}",
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
                "file_path": segment_path
            })
            
            logger.info(f"Saved segment {i+1}: {start_time:.2f}s - {end_time:.2f}s ({end_time - start_time:.2f}s)")
        except Exception as e:
            logger.error(f"Error saving segment {i+1}: {e}")
    
    # Save segment info to JSON
    info_path = os.path.join(output_dir, "segment_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(segment_info, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved segment info to: {info_path}")
    
    return segment_info

async def transcribe_segment(audio_path, api_key):
    """
    Transcribe an audio segment using Sarvam's speech-to-text API (without translation).
    
    Args:
        audio_path: Path to the audio file
        api_key: Sarvam API key
        
    Returns:
        dict: Transcription results
    """
    logger.info(f"Transcribing segment: {audio_path}")
    
    # API endpoint for speech-to-text (not translation)
    api_url = "https://api.sarvam.ai/speech-to-text"
    
    headers = {
        "api-subscription-key": api_key
    }
    
    data = {
        "model": "saarika:v2",  # Updated model name as per error message
        "diarize": "true"  # Enable diarization
    }
    
    try:
        with open(audio_path, "rb") as audio_file:
            files = {
                "file": (os.path.basename(audio_path), audio_file, "audio/wav")
            }
            
            response = requests.post(api_url, headers=headers, files=files, data=data)
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                logger.info(f"Transcription successful: {result.get('transcript', '')[:50]}...")
                return result
            else:
                logger.error(f"Transcription failed: {response.status_code} - {response.text}")
                return None
    except Exception as e:
        logger.error(f"Error transcribing segment: {e}")
        return None

def process_segment_result(result, segment_info):
    """
    Process the result from Sarvam's speech-to-text API.
    
    Args:
        result: Raw result from the API
        segment_info: Information about the segment
        
    Returns:
        dict: Processed result with segments
    """
    if not result:
        return {
            "segment_id": segment_info["segment_id"],
            "original_start_time": segment_info["start_time"],
            "original_end_time": segment_info["end_time"],
            "transcript": "",
            "segments": []
        }
    
    # Extract transcript and language code from the response
    transcript = result.get("transcript", "")
    language_code = result.get("language_code", "")
    
    processed = {
        "segment_id": segment_info["segment_id"],
        "original_start_time": segment_info["start_time"],
        "original_end_time": segment_info["end_time"],
        "transcript": transcript,
        "language_code": language_code,
        "segments": []
    }
    
    # Check if diarization information is available
    if "diarization" in result and result["diarization"]:
        for speaker_segment in result["diarization"]:
            segment = {
                "speaker": speaker_segment.get("speaker", "SPEAKER_00"),
                "text": speaker_segment.get("text", ""),
                "start": speaker_segment.get("start", 0),
                "end": speaker_segment.get("end", 0)
            }
            processed["segments"].append(segment)
    else:
        # Create a single segment if no diarization is available
        processed["segments"].append({
            "speaker": "SPEAKER_00",
            "text": transcript,  # Use the transcript as the segment text
            "start": 0,
            "end": segment_info["duration"]
        })
    
    return processed

async def test_vad_with_stt(audio_path):
    """
    Test VAD segmentation with Sarvam speech-to-text.
    First segments the audio using VAD, then sends each segment to Sarvam for STT.
    
    Args:
        audio_path: Path to the audio file
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    logger.info(f"Testing VAD with Sarvam STT on audio file: {audio_path}")
    
    # Step 1: Segment audio with VAD
    segment_info = segment_audio_with_vad(audio_path)
    
    if not segment_info:
        logger.error("VAD segmentation failed or found no segments")
        return
    
    # Step 2: Process each segment with Sarvam STT
    all_results = []
    
    for segment in segment_info:
        segment_path = segment["file_path"]
        segment_id = segment["segment_id"]
        
        logger.info(f"Processing segment {segment_id} with Sarvam STT")
        
        try:
            # Call Sarvam STT on the segment
            segment_result = await transcribe_segment(segment_path, SARVAM_API_KEY)
            
            # Save raw segment results for debugging
            output_dir = os.path.join("test_outputs", "vad_stt_results")
            os.makedirs(output_dir, exist_ok=True)
            segment_raw_path = os.path.join(output_dir, f"{segment_id}_raw.json")
            with open(segment_raw_path, "w", encoding="utf-8") as f:
                json.dump(segment_result, f, indent=2, ensure_ascii=False)
            
            # Process the segment results
            processed_segment = process_segment_result(segment_result, segment)
            
            # Save processed segment results for debugging
            segment_processed_path = os.path.join(output_dir, f"{segment_id}_processed.json")
            with open(segment_processed_path, "w", encoding="utf-8") as f:
                json.dump(processed_segment, f, indent=2, ensure_ascii=False)
            
            all_results.append(processed_segment)
            
            logger.info(f"Successfully processed segment {segment_id}")
            
        except Exception as e:
            logger.error(f"Error processing segment {segment_id}: {e}")
    
    # Step 3: Combine all results
    combined_results = {
        "segments": [],
        "transcript": "",
        "language_code": None
    }
    
    for result in all_results:
        # Update language code if not set
        if not combined_results["language_code"] and result.get("language_code"):
            combined_results["language_code"] = result["language_code"]
        
        # Append transcript
        if result.get("transcript"):
            combined_results["transcript"] += result["transcript"] + " "
        
        # Adjust segment timestamps and add to combined results
        if "segments" in result and result["segments"]:
            logger.info(f"Adding {len(result['segments'])} segments from {result['segment_id']}")
            for segment in result["segments"]:
                # Adjust timestamps to account for segment start time
                segment["start"] += result["original_start_time"]
                segment["end"] += result["original_start_time"]
                combined_results["segments"].append(segment)
        else:
            logger.warning(f"No segments found in processed result for {result.get('segment_id', 'unknown')}")
    
    # Trim trailing space from transcript
    combined_results["transcript"] = combined_results["transcript"].strip()
    
    # Save combined results
    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    combined_output_path = os.path.join(output_dir, "vad_stt_combined_output.json")
    with open(combined_output_path, "w", encoding="utf-8") as f:
        json.dump(combined_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Combined VAD + STT results saved to: {combined_output_path}")
    logger.info(f"Total segments in combined results: {len(combined_results['segments'])}")
    
    return combined_results

if __name__ == "__main__":
    # Path to the audio file to test
    audio_path = "/Users/sandilya/Sandy/Startup Ideas/Speech Based/filmymojimiddleclassmadhu.mp3"
    
    # Run the VAD with STT test
    asyncio.run(test_vad_with_stt(audio_path))
