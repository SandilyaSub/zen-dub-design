"""
Time-aligned TTS module for adjusting synthesized speech to match original segment durations.

This module provides functionality to speed up or slow down synthesized speech segments
to match the exact duration of the original audio segments, maintaining temporal alignment.
"""

import os
import json
import logging
import tempfile
import subprocess
import math
from typing import Dict, List, Tuple, Optional, Union, Any
import librosa
import numpy as np
from pydub import AudioSegment

from utils.file_utils import get_ffmpeg_path
from utils.metadata_manager import update_metadata_section

logger = logging.getLogger(__name__)

def build_atempo_filters(speed_factor: float) -> str:
    """
    Build ffmpeg atempo filter string for the given speed factor.
    
    Args:
        speed_factor: Speed factor to apply (>1 speeds up, <1 slows down)
        
    Returns:
        str: ffmpeg filter string
    """
    filters = []
    
    # Handle speed factors outside the valid range for atempo (0.5-2.0)
    remaining_factor = speed_factor
    
    # For speeding up (factor > 1)
    while remaining_factor > 2.0:
        filters.append("atempo=2.0")
        remaining_factor /= 2.0
    
    # For slowing down (factor < 1)
    while remaining_factor < 0.5:
        filters.append("atempo=0.5")
        remaining_factor /= 0.5
    
    # Add the remaining factor
    filters.append(f"atempo={remaining_factor:.6f}")
    
    return ",".join(filters)

def adjust_segment_duration(
    input_path: str, 
    output_path: str, 
    target_duration: float,
    original_duration: Optional[float] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Adjust the duration of an audio segment to match the target duration.
    
    Args:
        input_path: Path to input audio file
        output_path: Path to save the adjusted audio file
        target_duration: Target duration in seconds
        original_duration: Original duration in seconds (if None, will be calculated)
        
    Returns:
        Tuple[bool, Dict]: Success status and metadata about the adjustment
    """
    # Get original duration if not provided
    if original_duration is None:
        try:
            audio = AudioSegment.from_file(input_path)
            original_duration = len(audio) / 1000  # Convert ms to seconds
        except Exception as e:
            logger.error(f"Error getting original duration: {str(e)}")
            return False, {"error": f"Error getting original duration: {str(e)}"}
    
    # Calculate speed factor
    if original_duration <= 0 or target_duration <= 0:
        logger.error(f"Invalid durations: original={original_duration}, target={target_duration}")
        return False, {"error": "Invalid durations"}
    
    speed_factor = original_duration / target_duration
    
    # Limit minimum speed factor to 0.9 to prevent excessive slowdown
    if speed_factor < 0.9:
        logger.info(f"Limiting speed factor from {speed_factor:.4f} to 0.9 to prevent excessive slowdown")
        speed_factor = 0.9
        
    logger.info(f"Adjusting segment duration: original={original_duration:.2f}s, target={target_duration:.2f}s, speed_factor={speed_factor:.4f}")
    
    # Build quality metrics
    quality_metrics = {
        "original_duration": original_duration,
        "target_duration": target_duration,
        "speed_factor": speed_factor,
    }
    
    # Determine quality level based on speed factor
    if 0.8 <= speed_factor <= 1.25:
        quality_metrics["quality_level"] = "good"
        quality_metrics["quality_score"] = 90
    elif 0.6 <= speed_factor < 0.8 or 1.25 < speed_factor <= 1.75:
        quality_metrics["quality_level"] = "acceptable"
        quality_metrics["quality_score"] = 70
    else:
        quality_metrics["quality_level"] = "poor"
        quality_metrics["quality_score"] = 50
        quality_metrics["warning"] = "Extreme speed adjustment may affect audio quality"
    
    # Build ffmpeg filter
    atempo_filter = build_atempo_filters(speed_factor)
    logger.info(f"Using ffmpeg filter: {atempo_filter}")
    
    # Run ffmpeg command
    ffmpeg_path = get_ffmpeg_path()
    ffmpeg_cmd = [
        ffmpeg_path,
        "-y",  # Overwrite output files
        "-i", input_path,
        "-filter:a", atempo_filter,
        "-acodec", "pcm_s16le",  # Use standard WAV format
        "-ar", "44100",  # 44.1kHz sample rate
        output_path
    ]
    
    try:
        # Run ffmpeg
        process = subprocess.run(
            ffmpeg_cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        # Verify the output file exists and has content
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error("Output file is empty or doesn't exist")
            return False, {"error": "Output file is empty or doesn't exist"}
        
        # Verify the output duration
        try:
            output_audio = AudioSegment.from_file(output_path)
            output_duration = len(output_audio) / 1000
            
            quality_metrics["output_duration"] = output_duration
            quality_metrics["duration_difference"] = abs(output_duration - target_duration)
            
            logger.info(f"Output duration: {output_duration:.2f}s (target: {target_duration:.2f}s, difference: {quality_metrics['duration_difference']:.2f}s)")
            
            # Update quality score based on actual result
            if quality_metrics["duration_difference"] > 0.5:
                quality_metrics["quality_score"] -= 10
                quality_metrics["warning"] = f"Duration difference ({quality_metrics['duration_difference']:.2f}s) exceeds 0.5s"
        except Exception as e:
            logger.warning(f"Error verifying output duration: {str(e)}")
        
        return True, quality_metrics
        
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg error: {e.stderr.decode()}")
        return False, {"error": f"ffmpeg error: {e.stderr.decode()}"}
    except Exception as e:
        logger.error(f"Error adjusting segment duration: {str(e)}")
        return False, {"error": f"Error adjusting segment duration: {str(e)}"}

def process_segments_with_time_alignment(
    session_id: str,
    output_dir: str,
    vad_segments_file: Optional[str] = None,
    tts_dir: Optional[str] = None,
    metadata_output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process all TTS segments to match the original segment durations.
    
    Args:
        session_id: Session ID
        output_dir: Base output directory
        vad_segments_file: Path to VAD segments JSON file (optional)
        tts_dir: Directory containing TTS segments (optional)
        metadata_output_path: Path to save alignment metadata (optional)
        
    Returns:
        Dict: Metadata about the time alignment process
    """
    # Set up paths
    if not tts_dir:
        tts_dir = os.path.join(output_dir, session_id, "tts")
    
    if not vad_segments_file:
        # Switch to diarization.json instead of segment_info.json
        vad_segments_file = os.path.join(output_dir, session_id, "diarization.json")
    
    if not metadata_output_path:
        metadata_output_path = os.path.join(tts_dir, "time_alignment_metadata.json")
    
    # Check if files exist
    if not os.path.exists(vad_segments_file):
        logger.error(f"Diarization segments file not found: {vad_segments_file}")
        return {"error": f"Diarization segments file not found: {vad_segments_file}"}
    
    if not os.path.exists(tts_dir):
        logger.error(f"TTS directory not found: {tts_dir}")
        return {"error": f"TTS directory not found: {tts_dir}"}
    
    # Load VAD segments
    try:
        with open(vad_segments_file, 'r') as f:
            loaded_data = json.load(f)
        
        # Check if this is a merged segments file
        if isinstance(loaded_data, dict) and 'merged_segments' in loaded_data:
            vad_segments = loaded_data['merged_segments']
            logger.info(f"Loaded {len(vad_segments)} merged segments from {vad_segments_file}")
        # Check if the loaded data is a dictionary with a 'segments' key (diarization.json format)
        elif isinstance(loaded_data, dict) and 'segments' in loaded_data:
            vad_segments = loaded_data['segments']
            logger.info(f"Loaded {len(vad_segments)} segments from diarization file {vad_segments_file}")
        else:
            # Assume it's a direct list of segments (old VAD format)
            vad_segments = loaded_data
            logger.info(f"Loaded {len(vad_segments)} VAD segments from {vad_segments_file}")
    except Exception as e:
        logger.error(f"Error loading segments: {str(e)}")
        return {"error": f"Error loading segments: {str(e)}"}
    
    # Initialize metadata
    alignment_metadata = {
        "session_id": session_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0",
        "global_stats": {
            "total_segments": len(vad_segments),
            "processed_segments": 0,
            "successful_segments": 0,
            "failed_segments": 0,
            "avg_speed_factor": 0,
            "max_speed_factor": 0,
            "min_speed_factor": float('inf'),
            "segments_within_ideal_range": 0,
            "segments_within_acceptable_range": 0,
            "segments_outside_acceptable_range": 0
        },
        "segments": []
    }
    
    # Process each segment
    speed_factors = []
    
    for segment in vad_segments:
        # Handle both dictionary segments and string segment IDs
        if isinstance(segment, dict):
            segment_id = segment.get("segment_id")
            original_duration = segment.get("duration", 0)
            
            # Skip segments that are actually top-level keys from the merged file
            if segment_id in ["transcript", "translated_transcript", "original_segment_count", 
                             "merged_segment_count", "max_silence_ms"]:
                logger.info(f"Skipping non-segment key: {segment_id}")
                continue
                
            if not segment_id:
                logger.warning(f"Skipping segment with missing ID: {segment}")
                continue
                
            # Check for original segments within this segment (for merged segments)
            original_segments = segment.get('original_segments', [])
        else:
            # If segment is a string, it's likely just a segment ID
            segment_id = segment
            original_duration = 0  # We don't have duration info for string segments
            original_segments = []
            logger.warning(f"Received string segment ID instead of dictionary: {segment_id}")
        
        # Find corresponding TTS file
        tts_file = None
        
        # Check for both original segment ID and merged segment ID formats
        possible_prefixes = [
            f"segment_{segment_id}",  # Original format (segment_seg_000)
            f"segment_merged_{segment_id}"  # Merged format (segment_merged_000)
        ]
        
        # If this is a merged segment file, also look for the original segments
        for orig_seg in original_segments:
            if isinstance(orig_seg, dict):
                orig_id = orig_seg.get('segment_id')
                if orig_id:
                    possible_prefixes.append(f"segment_{orig_id}")
        
        # Check for files with any of the possible prefixes
        for filename in os.listdir(tts_dir):
            for prefix in possible_prefixes:
                if filename.startswith(prefix) and (filename.endswith(".wav") or filename.endswith(".mp3")):
                    tts_file = os.path.join(tts_dir, filename)
                    logger.info(f"Found TTS file for segment {segment_id}: {filename}")
                    break
            if tts_file:
                break
        
        if not tts_file:
            logger.warning(f"TTS file not found for segment {segment_id}")
            
            # Add to metadata
            alignment_metadata["segments"].append({
                "segment_id": segment_id,
                "original_duration": original_duration,
                "status": "skipped",
                "reason": "TTS file not found"
            })
            
            alignment_metadata["global_stats"]["failed_segments"] += 1
            continue
        
        # Process this segment
        logger.info(f"Processing segment {segment_id} with original duration {original_duration}s")
        
        # Create output path (ensure it's different from the input file)
        tts_file_name = os.path.basename(tts_file)
        output_file = os.path.join(tts_dir, f"segment_{segment_id}_time_aligned.wav")
        
        # Create a temporary file for processing to avoid in-place editing
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_output = temp_file.name
        
        # Adjust duration using the temporary file
        success, segment_metadata = adjust_segment_duration(
            tts_file,
            temp_output,
            original_duration
        )
        
        # If successful, copy the temp file to the final output location
        if success:
            try:
                import shutil
                shutil.copy2(temp_output, output_file)
                os.remove(temp_output)  # Clean up temp file
            except Exception as e:
                logger.error(f"Error copying temp file to output: {str(e)}")
                success = False
        else:
            # Clean up temp file in case of failure
            try:
                os.remove(temp_output)
            except:
                pass
        
        # Update metadata
        segment_metadata["segment_id"] = segment_id
        segment_metadata["status"] = "success" if success else "failed"
        segment_metadata["input_file"] = tts_file
        segment_metadata["output_file"] = output_file if success else None
        
        alignment_metadata["segments"].append(segment_metadata)
        alignment_metadata["global_stats"]["processed_segments"] += 1
        
        if success:
            alignment_metadata["global_stats"]["successful_segments"] += 1
            
            # Update speed factor statistics
            speed_factor = segment_metadata.get("speed_factor", 0)
            speed_factors.append(speed_factor)
            
            alignment_metadata["global_stats"]["max_speed_factor"] = max(
                alignment_metadata["global_stats"]["max_speed_factor"],
                speed_factor
            )
            
            alignment_metadata["global_stats"]["min_speed_factor"] = min(
                alignment_metadata["global_stats"]["min_speed_factor"],
                speed_factor
            )
            
            # Update quality range counts
            quality_level = segment_metadata.get("quality_level")
            if quality_level == "good":
                alignment_metadata["global_stats"]["segments_within_ideal_range"] += 1
            elif quality_level == "acceptable":
                alignment_metadata["global_stats"]["segments_within_acceptable_range"] += 1
            else:
                alignment_metadata["global_stats"]["segments_outside_acceptable_range"] += 1
        else:
            alignment_metadata["global_stats"]["failed_segments"] += 1
    
    # Calculate average speed factor
    if speed_factors:
        alignment_metadata["global_stats"]["avg_speed_factor"] = sum(speed_factors) / len(speed_factors)
    
    # If no segments were processed successfully, set min_speed_factor to 0
    if alignment_metadata["global_stats"]["min_speed_factor"] == float('inf'):
        alignment_metadata["global_stats"]["min_speed_factor"] = 0
    
    # Save metadata using the metadata manager
    try:
        # Extract session_id from the output path
        # Assuming the path format is: outputs/session_id/...
        path_parts = os.path.normpath(output_dir).split(os.sep)
        if len(path_parts) >= 2:
            session_id = path_parts[1]  # The second part should be the session_id
            
            # Use the metadata manager to update the time_alignment section
            update_metadata_section(session_id, "time_alignment", alignment_metadata)
            logger.info(f"Time alignment metadata saved using append-only approach")
            
            # Still save the standalone metadata file for backward compatibility
            with open(metadata_output_path, 'w') as f:
                json.dump(alignment_metadata, f, indent=2)
            logger.info(f"Time alignment metadata also saved to standalone file: {metadata_output_path}")
        else:
            logger.warning(f"Could not extract session_id from path: {output_dir}, saving only to standalone file")
            with open(metadata_output_path, 'w') as f:
                json.dump(alignment_metadata, f, indent=2)
            logger.info(f"Time alignment metadata saved to {metadata_output_path}")
    except Exception as e:
        logger.error(f"Error saving time alignment metadata: {str(e)}")
        # Fall back to direct file write
        with open(metadata_output_path, 'w') as f:
            json.dump(alignment_metadata, f, indent=2)
        logger.info(f"Time alignment metadata saved to {metadata_output_path} (fallback)")
    
    return alignment_metadata

def stitch_time_aligned_segments(
    session_id: str,
    output_dir: str,
    alignment_metadata: Optional[Dict] = None,
    metadata_file: Optional[str] = None,
    output_file: Optional[str] = None,
    original_audio_path: Optional[str] = None
) -> str:
    """
    Stitch time-aligned segments together with precise silence padding to match original audio timing.
    
    Args:
        session_id: Session ID
        output_dir: Base output directory
        alignment_metadata: Time alignment metadata (optional)
        metadata_file: Path to time alignment metadata file (optional)
        output_file: Path to save the stitched audio (optional)
        original_audio_path: Path to the original audio file (optional)
        
    Returns:
        str: Path to the stitched audio file
    """
    # Set up paths
    tts_dir = os.path.join(output_dir, session_id, "tts")
    synthesis_dir = os.path.join(output_dir, session_id, "synthesis")
    
    if not metadata_file:
        metadata_file = os.path.join(synthesis_dir, "time_alignment_metadata.json")
    
    if not output_file:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(tts_dir, f"final_output_time_aligned_{timestamp}.wav")
    
    # Determine original audio path if not provided
    if not original_audio_path:
        original_audio_path = os.path.join(output_dir, session_id, "audio", f"session_{session_id}.wav")
    
    # Get original audio duration
    original_duration = None
    try:
        if os.path.exists(original_audio_path):
            original_audio = AudioSegment.from_file(original_audio_path)
            original_duration = len(original_audio) / 1000  # Convert to seconds
            logger.info(f"Original audio duration: {original_duration:.2f}s")
        else:
            logger.warning(f"Original audio file not found: {original_audio_path}")
    except Exception as e:
        logger.error(f"Error getting original audio duration: {str(e)}")
    
    # Load metadata if not provided
    if not alignment_metadata:
        try:
            with open(metadata_file, 'r') as f:
                alignment_metadata = json.load(f)
            
            logger.info(f"Loaded time alignment metadata from {metadata_file}")
        except Exception as e:
            logger.error(f"Error loading time alignment metadata: {str(e)}")
            return None
    
    # Get segments
    segments = alignment_metadata.get("segments", [])
    if not segments:
        logger.error("No segments found in metadata")
        return None
    
    # Sort segments by segment_id
    segments.sort(key=lambda x: x.get("segment_id", ""))
    
    # Load the segments to get original timing - prioritize merged segments over regular diarization
    merged_diarization_file = os.path.join(output_dir, session_id, "diarization_translated_merged.json")
    diarization_file = os.path.join(output_dir, session_id, "diarization.json")
    vad_segments_file = os.path.join(output_dir, session_id, "vad_segments", "segment_info.json")
    timing_segments = []
    
    # First try: Look for merged diarization file
    if os.path.exists(merged_diarization_file):
        try:
            with open(merged_diarization_file, 'r') as f:
                loaded_data = json.load(f)
            
            # Check if the loaded data has merged_segments key
            if isinstance(loaded_data, dict) and 'merged_segments' in loaded_data:
                timing_segments = loaded_data['merged_segments']
                logger.info(f"Loaded {len(timing_segments)} merged segments from {merged_diarization_file}")
            else:
                logger.warning(f"Merged diarization file does not contain merged_segments key")
        except Exception as e:
            logger.error(f"Error loading merged diarization segments: {str(e)}")
    
    # Second try: Look for regular diarization.json as fallback
    if not timing_segments and os.path.exists(diarization_file):
        try:
            with open(diarization_file, 'r') as f:
                loaded_data = json.load(f)
            
            # Check if the loaded data is a dictionary with a 'segments' key (diarization.json format)
            if isinstance(loaded_data, dict) and 'segments' in loaded_data:
                timing_segments = loaded_data['segments']
                logger.info(f"Loaded {len(timing_segments)} segments from diarization file {diarization_file}")
            else:
                # Assume it's a direct list of segments
                timing_segments = loaded_data
                logger.info(f"Loaded {len(timing_segments)} segments from {diarization_file}")
        except Exception as e:
            logger.error(f"Error loading diarization segments: {str(e)}")
    
    # Third attempt: Try VAD segments file as fallback
    if not timing_segments and os.path.exists(vad_segments_file):
        try:
            with open(vad_segments_file, 'r') as f:
                loaded_data = json.load(f)
            
            # Check if the loaded data is a dictionary with a 'segments' key
            if isinstance(loaded_data, dict) and 'segments' in loaded_data:
                timing_segments = loaded_data['segments']
                logger.info(f"Loaded {len(timing_segments)} segments from VAD segments file {vad_segments_file}")
            else:
                # Assume it's a direct list of segments (old VAD format)
                timing_segments = loaded_data
                logger.info(f"Loaded {len(timing_segments)} VAD segments from {vad_segments_file}")
        except Exception as e:
            logger.error(f"Error loading VAD segments: {str(e)}")
    
    # If we still don't have segments, log a warning and proceed with sequential placement
    if not timing_segments:
        logger.warning(f"Could not find VAD segments file. Will use sequential placement.")
    
    # Create a mapping of segment_id to timing segment
    timing_segment_map = {seg.get("segment_id", ""): seg for seg in timing_segments}
    
    # Initialize a blank canvas for precise positioning
    # Use original duration if available, otherwise use the end time of the last timing segment
    if original_duration:
        # Add a small buffer to ensure we don't cut off any audio due to rounding errors
        final_duration_ms = int(original_duration * 1000) + 10  # Add 10ms buffer for precision
        logger.info(f"Using original audio duration: {original_duration}s ({final_duration_ms}ms)")
    elif timing_segments:
        last_end_time = max(seg.get("end_time", 0) for seg in timing_segments)
        # Add a larger buffer when we don't have the original duration
        final_duration_ms = int(last_end_time * 1000) + 1500  # Add 1.5 second buffer
        logger.info(f"Using last timing segment end time: {last_end_time}s with buffer ({final_duration_ms}ms)")
    else:
        # Fallback: Use the sum of all segment durations plus some buffer
        final_duration_ms = int(sum(seg.get("output_duration", 0) for seg in segments) * 1000) + 2000
        logger.info(f"Using fallback duration calculation: {final_duration_ms}ms")
    
    # Create a silent canvas of the full duration
    canvas = AudioSegment.silent(duration=final_duration_ms)
    
    # Process each segment
    for i, segment in enumerate(segments):
        # Handle both dictionary segments and string segment IDs
        if isinstance(segment, dict):
            segment_id = segment.get("segment_id")
            status = segment.get("status")
            
            # Get output file
            output_file_path = segment.get("output_file")
        else:
            # If segment is a string, it's likely just a segment ID
            segment_id = segment
            status = None
            output_file_path = None
            logger.warning(f"Received string segment ID instead of dictionary: {segment_id}")
            continue  # Skip string segments as they don't have the necessary data
        
        if status != "success":
            logger.warning(f"Skipping segment {segment_id} with status {status}")
            continue
        
        if not output_file_path or not os.path.exists(output_file_path):
            logger.warning(f"Output file not found for segment {segment_id}: {output_file_path}")
            continue
        
        # Get corresponding segment for timing
        timing_segment = timing_segment_map.get(segment_id)
        if not timing_segment:
            logger.warning(f"No timing segment found for {segment_id}, using sequential placement")
            # Fallback: place sequentially
            if i > 0:
                prev_segment = segments[i-1]
                if isinstance(prev_segment, dict):
                    prev_end_time = prev_segment.get("output_duration", 0) * 1000
                    position_ms = int(prev_end_time)
                else:
                    position_ms = 0
            else:
                position_ms = 0
        else:
            # Use exact timing from timing segment
            if isinstance(timing_segment, dict):
                position_ms = int(timing_segment.get("start_time", 0) * 1000)
            else:
                position_ms = 0
            logger.info(f"Positioning segment {segment_id} at {position_ms/1000:.2f}s based on timing")
        
        # Load segment audio
        try:
            segment_audio = AudioSegment.from_file(output_file_path)
            # Overlay segment at the exact position
            canvas = canvas.overlay(segment_audio, position=position_ms)
            
            logger.info(f"Added segment {segment_id} to position {position_ms/1000:.2f}s (duration: {len(segment_audio)/1000:.2f}s)")
        except Exception as e:
            logger.error(f"Error processing segment {segment_id}: {str(e)}")
    
    # Trim to match original duration exactly if needed
    if original_duration and len(canvas) > original_duration * 1000:
        target_duration_ms = int(original_duration * 1000)
        logger.info(f"Trimmed output to match original duration exactly: {original_duration}s")
        canvas = canvas[:target_duration_ms]
    
    # Check if we should add background music
    background_file = os.path.join(output_dir, session_id, "music", "background.wav")
    metadata_file = os.path.join(output_dir, session_id, "music", "metadata.json")
    user_metadata_file = os.path.join(output_dir, session_id, "metadata.json")
    
    # Check user preference for background music
    user_wants_background = False
    if os.path.exists(user_metadata_file):
        try:
            with open(user_metadata_file, 'r') as f:
                user_metadata = json.load(f)
            user_wants_background = user_metadata.get('preserve_background_music', False)
            logger.info(f"User preference for background music: {user_wants_background}")
        except Exception as e:
            logger.error(f"Error reading user metadata: {str(e)}")
    
    # Only proceed with background processing if user enabled it
    if not user_wants_background:
        logger.info("Background music disabled by user preference")
    elif os.path.exists(background_file) and os.path.exists(metadata_file):
        logger.info(f"Found background music file: {background_file}")
        
        try:
            # Analyze metadata
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            # Check if background is significant
            has_significant_background = metadata.get("analysis", {}).get("has_significant_background", False)
            
            if has_significant_background:
                logger.info("Significant background detected, applying background music")
                
                # Load background music
                background_audio = AudioSegment.from_file(background_file)
                
                # Get volume levels from metadata
                vocals_db = metadata.get("stats", {}).get("vocals_rms_db", -20)
                background_db = metadata.get("stats", {}).get("background_rms_db", -30)
                
                # Use the original audio levels directly
                # Calculate the adjustment needed to bring the background to its original level
                adjustment_db = background_db - background_db  # This will be 0, preserving the original level
                
                logger.info(f"Using original audio levels - vocals: {vocals_db}dB, background: {background_db}dB")
                
                # Adjust background volume
                adjusted_background = background_audio + adjustment_db
                
                # Resize background to match canvas length
                if len(adjusted_background) > len(canvas):
                    adjusted_background = adjusted_background[:len(canvas)]
                else:
                    # Loop background if needed
                    loops_needed = math.ceil(len(canvas) / len(adjusted_background))
                    looped_background = adjusted_background * loops_needed
                    adjusted_background = looped_background[:len(canvas)]
                
                # Mix background with translated audio
                canvas = canvas.overlay(adjusted_background)
                logger.info(f"Added background music with {adjustment_db}dB adjustment")
            else:
                logger.info("No significant background detected, skipping background music")
        except Exception as e:
            logger.error(f"Error processing background music: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Get final duration
    final_duration = len(canvas) / 1000
    if original_duration is not None:
        logger.info(f"Final output duration: {final_duration:.3f}s (target: {original_duration:.3f}s)")
    else:
        logger.info(f"Final output duration: {final_duration:.3f}s (target duration unknown)")
    
    # Save combined audio
    try:
        canvas.export(output_file, format="wav")
        logger.info(f"Time-aligned audio saved to {output_file} (duration: {len(canvas)/1000:.2f}s)")
        return output_file
    except Exception as e:
        logger.error(f"Error saving time-aligned audio: {str(e)}")
        return None

# Add missing import
import datetime
