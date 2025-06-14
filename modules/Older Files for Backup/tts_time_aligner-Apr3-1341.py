import os
import json
import logging
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import TTS modules
from modules.sarvam_tts import synthesize_speech as sarvam_synthesize
from modules.cartesia_tts import synthesize_speech as cartesia_synthesize

def get_audio_duration(audio_path):
    """Get the duration of an audio file in seconds."""
    try:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # Convert ms to seconds
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
        return None

def create_silence(duration_ms, sample_rate=22050):
    """Create a silent audio segment of specified duration."""
    try:
        silence = AudioSegment.silent(duration=duration_ms)
        return silence
    except Exception as e:
        logger.error(f"Error creating silence: {e}")
        return None

def save_synthesis_details(output_path, segments, language, speaker, model, final_audio_path):
    """
    Save synthesis details to a JSON file in the synthesis directory.
    
    Args:
        output_path: Path where the synthesis details will be saved
        segments: List of processed segments
        language: Target language
        speaker: Speaker voice used
        model: TTS model used
        final_audio_path: Path to the final output audio file
    """
    synthesis_dir = os.path.dirname(output_path)
    details_path = os.path.join(synthesis_dir, "synthesis_details.json")
    
    # Get timestamp from output filename
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")
    
    # Calculate session ID from output path
    session_id = os.path.basename(os.path.dirname(synthesis_dir))
    
    # Get final audio file size
    audio_size = os.path.getsize(final_audio_path) if os.path.exists(final_audio_path) else 0
    
    # Calculate total durations
    total_input_duration = 0.0
    total_output_duration = 0.0
    total_padding_duration = 0.0
    
    # Create segment details
    segment_details = []
    for i, segment in enumerate(segments):
        segment_id = segment.get("segment_id", i)
        start_time = float(segment.get("start", 0))
        end_time = float(segment.get("end", 0))
        input_duration = end_time - start_time
        
        # Get output audio duration
        segment_output_path = os.path.join(synthesis_dir, "temp_segments", f"segment_{segment_id}_final.wav")
        output_duration = get_audio_duration(segment_output_path) or input_duration
        
        # Calculate padding
        if i > 0:
            prev_segment = segments[i-1]
            prev_end = float(prev_segment.get("end", 0))
            silence_duration = start_time - prev_end
            if silence_duration > 0:
                total_padding_duration += silence_duration
        
        total_input_duration += input_duration
        total_output_duration += output_duration
        
        segment_details.append({
            "index": i,
            "start_time": start_time,
            "end_time": end_time,
            "input_duration": input_duration,
            "output_duration": output_duration,
            "text": segment.get("translated_text", segment.get("text", "")),  # Use translated text if available, fallback to original text
            "padding_duration": silence_duration if i > 0 else 0.0,
            "speaker": segment.get("speaker", ""),
            "gender": segment.get("gender", "")
        })
    
    # Create and save synthesis details
    synthesis_details = {
        "session_id": session_id,
        "timestamp": timestamp,
        "provider": "sarvam",
        "language": language,
        "speaker": speaker,
        "model": model,
        "segments": segment_details,
        "final_output": {
            "file": os.path.basename(final_audio_path),
            "format": os.path.splitext(final_audio_path)[1][1:],
            "total_duration": total_output_duration,
            "segments_count": len(segments),
            "size_bytes": audio_size,
            "padding_duration": total_padding_duration
        },
        "processing_summary": {
            "total_segments": len(segments),
            "total_duration": total_output_duration,
            "input_duration": total_input_duration,
            "padding_duration": total_padding_duration,
            "average_pace": total_output_duration / total_input_duration if total_input_duration > 0 else 0.0,
            "average_segment_duration": total_output_duration / len(segments) if segments else 0.0
        }
    }
    
    try:
        with open(details_path, 'w', encoding='utf-8') as f:
            json.dump(synthesis_details, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved synthesis details to {details_path}")
    except Exception as e:
        logger.error(f"Error saving synthesis details: {e}")

def time_aligned_tts_cartesia(segments, output_path, voice_id=None, bit_rate=128000, sample_rate=44100):
    """
    Generate time-aligned TTS using Cartesia API with specified segment durations.
    
    Args:
        segments: List of diarization segments with timing information
        output_path: Path to save the final merged audio
        voice_id: Voice ID to use
        bit_rate: Audio bit rate
        sample_rate: Audio sample rate
        
    Returns:
        bool: Success status
    """
    try:
        logger.info(f"Generating time-aligned TTS with Cartesia for {len(segments)} segments")
        
        # Create a temporary directory for segment files
        temp_dir = os.path.join(os.path.dirname(output_path), "temp_segments")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Final merged audio
        merged_audio = AudioSegment.empty()
        last_end_time = 0
        
        for i, segment in enumerate(segments):
            segment_id = segment.get("segment_id", i)
            start_time = float(segment.get("start", 0))
            end_time = float(segment.get("end", 0))
            text = segment.get("text", "")
            
            # Calculate segment duration
            segment_duration = end_time - start_time
            
            # Skip segments with zero or negative duration
            if segment_duration <= 0:
                logger.warning(f"Segment {segment_id} has invalid duration: {segment_duration}s. Skipping.")
                continue
            
            # Add silence if there's a gap
            if start_time > last_end_time:
                silence_duration = (start_time - last_end_time) * 1000  # Convert to ms
                silence = create_silence(silence_duration)
                merged_audio += silence
                logger.info(f"Added {silence_duration/1000:.2f}s silence before segment {segment_id}")
            
            # Skip empty segments
            if not text.strip():
                # Add silence for the duration of this segment
                silence = create_silence(segment_duration * 1000)
                merged_audio += silence
                last_end_time = end_time
                logger.info(f"Added {segment_duration:.2f}s silence for empty segment {segment_id}")
                continue
            
            # Generate TTS for this segment with specified duration
            segment_output_path = os.path.join(temp_dir, f"segment_{segment_id}.mp3")
            
            # Cartesia allows specifying duration directly
            success = cartesia_synthesize(
                text=text,
                output_path=segment_output_path,
                voice_id=voice_id,
                bit_rate=bit_rate,
                sample_rate=sample_rate,
                duration=segment_duration if segment_duration > 0 else 1.0  # Avoid division by zero
            )
            
            if not success:
                logger.error(f"Failed to synthesize segment {segment_id}")
                continue
            
            # Add the segment to merged audio
            segment_audio = AudioSegment.from_file(segment_output_path)
            merged_audio += segment_audio
            
            # Update last end time
            last_end_time = end_time
            
            logger.info(f"Processed segment {segment_id}: {start_time:.2f}s - {end_time:.2f}s")
        
        # Save the final merged audio
        merged_audio.export(output_path, format="mp3")
        logger.info(f"Saved time-aligned audio to {output_path}")
        
        # Clean up temporary files
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in time-aligned TTS with Cartesia: {e}")
        return False

def time_aligned_tts_sarvam(segments, output_path, language, speaker=None):
    """
    Generate time-aligned TTS using Sarvam API with the specified algorithm.
    
    Args:
        segments: List of diarization segments with timing information
        output_path: Path to save the final merged audio
        language: Target language
        speaker: Speaker voice to use
        
    Returns:
        bool: Success status
    """
    try:
        logger.info(f"Generating time-aligned TTS with Sarvam for {len(segments)} segments")
        
        # Create a temporary directory for segment files
        temp_dir = os.path.join(os.path.dirname(output_path), "temp_segments")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Get model configuration
        model = os.getenv('SARVAM_TTS_MODEL', 'bulbul:v2')
        
        # Final merged audio
        merged_audio = AudioSegment.empty()
        current_position = 0  # Current position in the output audio (ms)
        
        # Process each segment and collect timing information
        segment_details = []
        last_end_time = 0
        
        for i, segment in enumerate(segments):
            segment_id = f"seg_{i+1}"
            start_time = float(segment.get("start", 0))
            end_time = float(segment.get("end", 0))
            text = segment.get("translated_text", segment.get("text", ""))  # Use translated text if available, fallback to original text
            speaker_info = segment.get("speaker", "")
            gender = segment.get("gender", "")
            
            # Calculate segment duration in seconds
            input_duration = end_time - start_time
            
            # Add logging for debugging
            logger.info(f"Processing segment {segment_id}: start={start_time:.2f}, end={end_time:.2f}, input_duration={input_duration:.2f}")
            logger.info(f"Text: {text[:50]}...")
            logger.info(f"Speaker: {speaker_info}, Gender: {gender}")
            
            # Skip segments with zero or negative duration
            if input_duration <= 0:
                logger.warning(f"Segment {segment_id} has invalid duration: {input_duration:.2f}s. Skipping.")
                continue
            
            # Skip empty segments
            if not text.strip():
                # Add silence for the duration of this segment
                silence_duration = input_duration * 1000  # Convert to ms
                silence = create_silence(silence_duration)
                merged_audio += silence
                current_position += silence_duration
                logger.info(f"Added {input_duration:.2f}s silence for empty segment {segment_id}")
                continue
            
            # Add silence if there's a gap between current position and segment start
            start_time_ms = start_time * 1000
            if start_time_ms > current_position:
                silence_duration = start_time_ms - current_position
                silence = create_silence(silence_duration)
                merged_audio += silence
                current_position += silence_duration
                logger.info(f"Added {silence_duration/1000:.2f}s silence before segment {segment_id}")
            
            # Get translated text for TTS
            translated_text = segment.get("translated_text", "")
            if not translated_text:
                logger.error(f"No translated text found for segment {segment_id}")
                continue
            
            # Generate initial TTS with default pace
            segment_output_path = os.path.join(temp_dir, f"segment_{segment_id}_initial.wav")
            
            # Get speaker voice based on gender from speakers dictionary
            speaker = None
            if speaker_info:
                # Get gender from speakers dictionary
                speaker_gender = None
                if "speakers" in diarization_data and speaker_info in diarization_data["speakers"]:
                    speaker_gender = diarization_data["speakers"][speaker_info].get("gender", "").lower()
                
                # Choose speaker based on gender if available
                if speaker_gender == "f":
                    speaker = "anushka"  # Default female voice
                elif speaker_gender == "m":
                    speaker = "abhilash"  # Default male voice
            
            # Generate initial TTS with default pace (1.0)
            success = sarvam_synthesize(
                text=translated_text,  # Use translated text for TTS
                language=language,
                output_path=segment_output_path,
                speaker=speaker,
                model=model,
                pace=1.0  # Start with default pace
            )
            
            if not success:
                logger.error(f"Failed to synthesize initial segment {segment_id} with text: {translated_text[:50]}...")
                continue
            
            try:
                # Get initial audio duration
                initial_audio = AudioSegment.from_file(segment_output_path)
                initial_duration = initial_audio.duration_seconds
                
                # Calculate target duration (original segment duration)
                target_duration = input_duration
                
                # Calculate pace adjustment
                target_pace = 1.0  # Start with default pace
                max_iterations = 5  # Maximum number of iterations to try
                tolerance = 0.1  # Acceptable duration difference in seconds
                
                for iteration in range(max_iterations):
                    # Calculate current pace adjustment
                    current_pace = target_pace
                    
                    # Generate TTS with adjusted pace
                    adjusted_output_path = os.path.join(temp_dir, f"segment_{segment_id}_iter_{iteration}.wav")
                    success = sarvam_synthesize(
                        text=translated_text,  # Use translated text for TTS
                        language=language,
                        output_path=adjusted_output_path,
                        speaker=speaker,
                        model=model,
                        pace=current_pace
                    )
                    
                    if not success:
                        logger.error(f"Failed to synthesize segment {segment_id} with pace {current_pace}")
                        break
                    
                    try:
                        # Get adjusted audio duration
                        adjusted_audio = AudioSegment.from_file(adjusted_output_path)
                        adjusted_duration = adjusted_audio.duration_seconds
                        
                        # Calculate duration difference
                        duration_diff = abs(target_duration - adjusted_duration)
                        
                        logger.info(f"Iteration {iteration}: Target={target_duration:.2f}s, Current={adjusted_duration:.2f}s, Diff={duration_diff:.2f}s")
                        
                        # Check if we're within tolerance
                        if duration_diff <= tolerance:
                            logger.info(f"Achieved target duration within tolerance after {iteration} iterations")
                            # Use this as our final audio
                            final_audio = adjusted_audio
                            final_duration = adjusted_duration
                            break
                        
                        # Calculate new pace based on duration difference
                        if adjusted_duration > target_duration:
                            # Too slow, increase pace
                            target_pace = current_pace * (target_duration / adjusted_duration)
                        else:
                            # Too fast, decrease pace
                            target_pace = current_pace * (target_duration / adjusted_duration)
                            
                        # Ensure pace stays within reasonable bounds
                        target_pace = max(0.5, min(2.0, target_pace))
                        
                    except Exception as e:
                        logger.error(f"Error processing adjusted audio for segment {segment_id}: {e}")
                        break
                
                # If we didn't break out of the loop, use the last iteration
                if 'final_audio' not in locals():
                    final_audio = adjusted_audio
                    final_duration = adjusted_duration
                    logger.warning(f"Reached max iterations without achieving target duration for segment {segment_id}")
                
                # Add the segment to merged audio
                merged_audio += final_audio
                current_position += final_duration * 1000
                
                # Save segment details
                segment_details.append({
                    "id": segment_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": final_duration,
                    "text": translated_text,  # Save the translated text
                    "speaker": speaker,
                    "gender": speaker_gender if speaker_gender else "",
                    "pace": current_pace
                })
                
                logger.info(f"Processed segment {segment_id}: {start_time:.2f}s - {end_time:.2f}s")
                logger.info(f"Final segment duration: {final_duration:.2f}s with pace {current_pace:.2f}")
                
            except Exception as e:
                logger.error(f"Error processing segment {segment_id}: {e}")
                continue
            
            # Update last end time
            last_end_time = end_time
        
        # Save the final merged audio
        merged_audio.export(output_path, format="wav")
        logger.info(f"Saved time-aligned audio to {output_path}")
        
        # Save synthesis details
        save_synthesis_details(
            os.path.dirname(output_path),
            segment_details,
            language,
            speaker,
            model,
            os.path.basename(output_path)
        )
        
        # Clean up temporary files
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in time-aligned TTS with Sarvam: {e}")
        return False

def time_aligned_tts(diarization_data, output_path, language, provider="sarvam", voice_id=None, options=None):
    """
    Generate time-aligned TTS from diarization data.
    
    Args:
        diarization_data: Diarization data with segments
        output_path: Path to save the final merged audio
        language: Target language
        provider: TTS provider to use (sarvam or cartesia)
        voice_id: Voice ID to use
        options: Additional options for the TTS engine
        
    Returns:
        bool: Success status
    """
    try:
        # Extract segments from diarization data
        segments = diarization_data.get("segments", [])
        
        if not segments:
            logger.error("No segments found in diarization data")
            return False
        
        # Default options
        if options is None:
            options = {}
        
        # Route to appropriate provider
        if provider == "cartesia":
            return time_aligned_tts_cartesia(
                segments=segments,
                output_path=output_path,
                voice_id=voice_id,
                bit_rate=options.get("bit_rate", 128000),
                sample_rate=options.get("sample_rate", 44100)
            )
        elif provider == "sarvam":
            return time_aligned_tts_sarvam(
                segments=segments,
                output_path=output_path,
                language=language,
                speaker=voice_id
            )
        else:
            logger.error(f"Invalid provider: {provider}")
            return False
            
    except Exception as e:
        logger.error(f"Error in time-aligned TTS: {e}")
        return False
