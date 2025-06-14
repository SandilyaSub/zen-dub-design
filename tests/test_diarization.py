#!/usr/bin/env python3
"""
Unit test for Sarvam diarization functionality.
This script tests the diarization process and displays the raw output from Sarvam.
It also implements VAD (Voice Activity Detection) for audio segmentation.
"""

import os
import json
import asyncio
import logging
import torch
import numpy as np
import librosa
import soundfile as sf
from io import BytesIO
from dotenv import load_dotenv
from modules.sarvam_speech import transcribe_with_diarization, process_diarization_results

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

async def test_vad_segmentation(audio_path):
    """
    Test VAD segmentation on an audio file.
    
    Args:
        audio_path: Path to the audio file
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    logger.info(f"Testing VAD segmentation with audio file: {audio_path}")
    
    # Segment audio with VAD
    segment_info = segment_audio_with_vad(audio_path)
    
    if not segment_info:
        logger.error("VAD segmentation failed or found no segments")
        return
    
    logger.info(f"VAD segmentation complete. Found {len(segment_info)} segments.")
    
    return segment_info

async def test_diarization(audio_path):
    """
    Test the diarization functionality with a given audio file.
    
    Args:
        audio_path (str): Path to the audio file to test
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    logger.info(f"Testing diarization with audio file: {audio_path}")
    
    # Call the transcribe_with_diarization function
    try:
        results = await transcribe_with_diarization(audio_path, SARVAM_API_KEY)
        
        # Save the raw results to a file
        output_dir = "test_outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        raw_output_path = os.path.join(output_dir, "raw_diarization_output.json")
        with open(raw_output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Raw diarization output saved to: {raw_output_path}")
        
        # Print the raw results
        logger.info("Raw diarization results:")
        logger.info(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Process the results
        processed_results = process_diarization_results(results)
        
        # Save the processed results to a file
        processed_output_path = os.path.join(output_dir, "processed_diarization_output.json")
        with open(processed_output_path, "w", encoding="utf-8") as f:
            json.dump(processed_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Processed diarization output saved to: {processed_output_path}")
        
        # Print the processed results
        logger.info("Processed diarization results:")
        logger.info(json.dumps(processed_results, indent=2, ensure_ascii=False))
        
        # Compare the structure with the expected format
        logger.info("Analyzing output structure...")
        
        # Check if the processed output matches the expected format
        expected_keys = ["segments", "transcript", "language_code"]
        missing_keys = [key for key in expected_keys if key not in processed_results]
        
        if missing_keys:
            logger.warning(f"Missing expected keys in processed output: {missing_keys}")
        else:
            logger.info("Processed output contains all expected keys")
        
        # Check segment structure
        if "segments" in processed_results and processed_results["segments"]:
            segment = processed_results["segments"][0]
            expected_segment_keys = ["speaker", "text", "start", "end"]
            missing_segment_keys = [key for key in expected_segment_keys if key not in segment]
            
            if missing_segment_keys:
                logger.warning(f"Missing expected keys in segment: {missing_segment_keys}")
            else:
                logger.info("Segment structure matches expected format")
        else:
            logger.warning("No segments found in processed output")
            
        return results, processed_results
        
    except Exception as e:
        logger.error(f"Error testing diarization: {e}")
        return None, None

async def test_vad_with_sarvam_diarization(audio_path):
    """
    Test VAD segmentation with Sarvam diarization.
    First segments the audio using VAD, then sends each segment to Sarvam for diarization.
    
    Args:
        audio_path: Path to the audio file
    """
    if not os.path.exists(audio_path):
        logger.error(f"Audio file not found: {audio_path}")
        return
    
    logger.info(f"Testing VAD with Sarvam diarization on audio file: {audio_path}")
    
    # Step 1: Segment audio with VAD
    segment_info = segment_audio_with_vad(audio_path)
    
    if not segment_info:
        logger.error("VAD segmentation failed or found no segments")
        return
    
    # Step 2: Process each segment with Sarvam diarization
    all_results = []
    
    for segment in segment_info:
        segment_path = segment["file_path"]
        segment_id = segment["segment_id"]
        
        logger.info(f"Processing segment {segment_id} with Sarvam diarization")
        
        try:
            # Call Sarvam diarization on the segment
            segment_results = await transcribe_with_diarization(segment_path, SARVAM_API_KEY)
            
            # Save raw segment results for debugging
            output_dir = os.path.join("test_outputs", "vad_segments_results")
            os.makedirs(output_dir, exist_ok=True)
            segment_raw_path = os.path.join(output_dir, f"{segment_id}_raw.json")
            with open(segment_raw_path, "w", encoding="utf-8") as f:
                json.dump(segment_results, f, indent=2, ensure_ascii=False)
            
            # Process the segment results
            processed_segment = process_diarization_results(segment_results)
            
            # Save processed segment results for debugging
            segment_processed_path = os.path.join(output_dir, f"{segment_id}_processed.json")
            with open(segment_processed_path, "w", encoding="utf-8") as f:
                json.dump(processed_segment, f, indent=2, ensure_ascii=False)
            
            # Add segment metadata
            processed_segment["segment_id"] = segment_id
            processed_segment["original_start_time"] = segment["start_time"]
            processed_segment["original_end_time"] = segment["end_time"]
            
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
            # If no segments but we have transcript, create a simple segment
            if result.get("transcript") and "original_start_time" in result and "original_end_time" in result:
                logger.info(f"Creating fallback segment for {result.get('segment_id')}")
                fallback_segment = {
                    "speaker": "SPEAKER_00",  # Default speaker
                    "text": result["transcript"],
                    "start": result["original_start_time"],
                    "end": result["original_end_time"]
                }
                combined_results["segments"].append(fallback_segment)
    
    # Trim trailing space from transcript
    combined_results["transcript"] = combined_results["transcript"].strip()
    
    # Save combined results
    output_dir = "test_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    combined_output_path = os.path.join(output_dir, "vad_sarvam_combined_output.json")
    with open(combined_output_path, "w", encoding="utf-8") as f:
        json.dump(combined_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Combined VAD + Sarvam results saved to: {combined_output_path}")
    logger.info(f"Total segments in combined results: {len(combined_results['segments'])}")
    
    return combined_results

if __name__ == "__main__":
    # Path to the audio file to test
    audio_path = "/Users/sandilya/Sandy/Startup Ideas/Speech Based/filmymojimiddleclassmadhu.mp3"
    
    # Run the tests
    # asyncio.run(test_diarization(audio_path))
    
    # Uncomment to run VAD segmentation test
    # asyncio.run(test_vad_segmentation(audio_path))
    
    # Uncomment to run VAD with Sarvam diarization test
    asyncio.run(test_vad_with_sarvam_diarization(audio_path))
