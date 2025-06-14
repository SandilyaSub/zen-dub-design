"""
Audio Separator Module

This module provides functionality to separate vocals (speech) from background music
in audio files. It uses Demucs, a state-of-the-art deep learning model for music source separation.
"""

import os
import json
import logging
import numpy as np
import subprocess
import shutil
import time
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("audio_separator")

def find_ffmpeg_paths():
    """
    Find the paths to ffmpeg and ffprobe executables.
    
    Returns:
        tuple: (ffmpeg_path, ffprobe_path)
    """
    # First try to find in PATH
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    
    # Log the paths
    logger.info(f"Found ffmpeg at: {ffmpeg_path}")
    logger.info(f"Found ffprobe at: {ffprobe_path}")
    
    # Set environment variables for subprocesses
    if ffmpeg_path:
        os.environ["FFMPEG_BINARY"] = ffmpeg_path
    if ffprobe_path:
        os.environ["FFPROBE_BINARY"] = ffprobe_path
    
    # Add the directory containing ffmpeg to PATH to help Demucs find it
    if ffmpeg_path:
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = f"{ffmpeg_dir}:{os.environ.get('PATH', '')}"
    
    return ffmpeg_path, ffprobe_path

def separate_vocals_from_background(input_file, output_dir, session_id):
    """
    Separate vocals (speech) from background music in an audio file using Demucs.
    
    Args:
        input_file (str): Path to the input audio file
        output_dir (str): Directory to save the separated audio files
        session_id (str): Session ID for file naming
        
    Returns:
        dict: Paths to the separated audio files and metadata
    """
    logger.info(f"Starting audio separation for {input_file}")
    
    # Find and set ffmpeg paths
    ffmpeg_path, ffprobe_path = find_ffmpeg_paths()
    
    if not ffmpeg_path:
        raise RuntimeError("ffmpeg not found. Please ensure it is installed and in your PATH.")
    
    try:
        # Create all necessary directories
        music_dir = os.path.join(output_dir, session_id, "music")
        audio_dir = os.path.join(output_dir, session_id, "audio")
        temp_dir = os.path.join(output_dir, session_id, "temp_demucs")
        
        os.makedirs(music_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Define output paths
        vocals_path = os.path.join(audio_dir, f"vocals_{session_id}.wav")
        background_path = os.path.join(music_dir, "background.wav")
        metadata_path = os.path.join(music_dir, "metadata.json")
        
        # Verify input file exists and is readable
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        # Run Demucs via subprocess for robustness
        logger.info(f"Running Demucs on {input_file}")
        start_time = time.time()
        
        cmd = [
            "python3", "-m", "demucs.separate",
            "--two-stems=vocals",  # Only separate vocals from everything else
            "-n", "htdemucs",      # Use the hybrid transformer model (best quality)
            "-o", temp_dir,        # Output directory
            input_file             # Input file
        ]
        
        # Run the command and capture output
        process = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        logger.info(f"Demucs stdout: {process.stdout}")
        if process.stderr:
            logger.warning(f"Demucs stderr: {process.stderr}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        logger.info(f"Demucs processing completed in {processing_time:.2f} seconds")
        
        # Find the output files
        # Demucs creates a directory structure: temp_dir/model_name/track_name/[vocals.wav, no_vocals.wav]
        input_basename = os.path.splitext(os.path.basename(input_file))[0]
        model_name = "htdemucs"
        
        demucs_output_dir = os.path.join(temp_dir, model_name, input_basename)
        demucs_vocals_path = os.path.join(demucs_output_dir, "vocals.wav")
        demucs_background_path = os.path.join(demucs_output_dir, "no_vocals.wav")
        
        if not os.path.exists(demucs_vocals_path) or not os.path.exists(demucs_background_path):
            # If the expected files don't exist, check if there's a different structure
            logger.warning(f"Expected output files not found at {demucs_output_dir}")
            # List all files in the temp directory to debug
            for root, dirs, files in os.walk(temp_dir):
                logger.info(f"Directory: {root}")
                for file in files:
                    logger.info(f"  File: {file}")
            
            # Try to find the files with a different pattern
            potential_dirs = list(Path(temp_dir).glob(f"*/*{input_basename}*"))
            if potential_dirs:
                demucs_output_dir = str(potential_dirs[0])
                logger.info(f"Found alternative output directory: {demucs_output_dir}")
                
                # Look for vocals and background files
                vocals_candidates = list(Path(demucs_output_dir).glob("*vocals*.wav"))
                background_candidates = list(Path(demucs_output_dir).glob("*no_vocals*.wav"))
                
                if vocals_candidates:
                    demucs_vocals_path = str(vocals_candidates[0])
                if background_candidates:
                    demucs_background_path = str(background_candidates[0])
        
        # Copy the separated files to our target locations
        if os.path.exists(demucs_vocals_path):
            shutil.copy(demucs_vocals_path, vocals_path)
            logger.info(f"Copied vocals to {vocals_path}")
        else:
            raise FileNotFoundError(f"Demucs vocals output not found at {demucs_vocals_path}")
        
        if os.path.exists(demucs_background_path):
            shutil.copy(demucs_background_path, background_path)
            logger.info(f"Copied background to {background_path}")
        else:
            raise FileNotFoundError(f"Demucs background output not found at {demucs_background_path}")
        
        # Get audio information using ffprobe
        duration = 0
        if ffprobe_path:
            try:
                cmd = [
                    ffprobe_path,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    input_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                duration = float(result.stdout.strip())
            except Exception as e:
                logger.warning(f"Could not get duration with ffprobe: {e}")
        
        # Calculate energy levels and percentages
        # Since we don't have direct access to the audio data through Python,
        # we'll use ffmpeg to get RMS values
        
        def get_rms_level(audio_file):
            """Get RMS level of an audio file using ffmpeg"""
            if not ffmpeg_path:
                return 0
            
            try:
                cmd = [
                    ffmpeg_path,
                    "-i", audio_file,
                    "-af", "volumedetect",
                    "-f", "null", "/dev/null"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                # Parse the output to find the RMS level
                for line in result.stderr.split('\n'):
                    if "mean_volume" in line:
                        # Extract the dB value
                        db_value = float(line.split(':')[1].strip().split(' ')[0])
                        # Convert from dB to linear scale
                        return 10 ** (db_value / 20)
                
                return 0
            except Exception as e:
                logger.warning(f"Could not get RMS level for {audio_file}: {e}")
                return 0
        
        # Get RMS levels
        vocals_rms = get_rms_level(vocals_path)
        background_rms = get_rms_level(background_path)
        original_rms = get_rms_level(input_file)
        
        # Calculate percentages
        if original_rms > 0:
            vocals_percentage = (vocals_rms / original_rms) * 100
            background_percentage = (background_rms / original_rms) * 100
        else:
            vocals_percentage = 0
            background_percentage = 0
        
        # Convert to dB
        vocals_db = 20 * np.log10(vocals_rms) if vocals_rms > 0 else -100
        background_db = 20 * np.log10(background_rms) if background_rms > 0 else -100
        
        # Determine if there's significant background
        threshold_db = -40.0
        has_significant_background = bool(background_db > threshold_db)  # Explicitly cast to Python bool
        
        # Import the metadata manager
        from utils.metadata_manager import update_metadata_section
        
        # Update metadata using the metadata manager instead of direct file write
        audio_separation_metadata = {
            "vocals_path": vocals_path,
            "background_path": background_path,
            "has_significant_background": has_significant_background,
            "separation_settings": {
                "model": model_name,
                "threshold_db": float(threshold_db)
            }
        }
        
        # Use the metadata manager to update the audio_separation section
        update_metadata_section(session_id, "audio_separation", audio_separation_metadata)
        logger.info(f"Updated metadata with audio separation information using append-only approach")
        
        # CRITICAL FIX: Create a separate metadata.json file in the music directory
        # This is needed for the time_aligned_tts module to find and use the background music
        music_metadata_path = os.path.join(music_dir, "metadata.json")
        music_metadata = {
            "analysis": {
                "has_significant_background": has_significant_background
            },
            "stats": {
                "vocals_rms_db": float(vocals_db),
                "background_rms_db": float(background_db),
                "vocals_percentage": float(vocals_percentage),
                "background_percentage": float(background_percentage)
            }
        }
        try:
            with open(music_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(music_metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Created metadata file in music directory: {music_metadata_path}")
        except Exception as e:
            logger.error(f"Error creating music metadata file: {str(e)}")
        
        # Clean up temporary files
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Could not clean up temporary directory: {e}")
        
        logger.info(f"Audio separation complete. Vocals: {vocals_path}, Background: {background_path}")
        logger.info(f"Vocal content: {vocals_percentage:.2f}%, Background content: {background_percentage:.2f}%")
        
        return {
            "vocals_path": vocals_path,
            "background_path": background_path,
            "has_significant_background": has_significant_background
        }
        
    except Exception as e:
        logger.error(f"Error separating audio: {str(e)}")
        raise

def analyze_audio_components(input_file):
    """
    Analyze an audio file to determine the presence of vocals and background music.
    Uses ffmpeg for analysis to avoid dependency on librosa.
    
    Args:
        input_file (str): Path to the input audio file
        
    Returns:
        dict: Analysis results
    """
    try:
        ffmpeg_path, _ = find_ffmpeg_paths()
        
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg not found. Please ensure it is installed and in your PATH.")
        
        # Use ffmpeg to analyze audio characteristics
        # Get spectral information
        cmd = [
            ffmpeg_path,
            "-i", input_file,
            "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.Flat_factor:file=-",
            "-f", "null", "/dev/null"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse the output to find the flatness factor (related to spectral flatness)
        spectral_flatness = 0
        for line in result.stderr.split('\n'):
            if "Flat_factor" in line:
                try:
                    spectral_flatness = float(line.split('=')[1].strip())
                except (ValueError, IndexError):
                    pass
        
        # Get zero crossing rate using ffmpeg
        cmd = [
            ffmpeg_path,
            "-i", input_file,
            "-af", "asetnsamples=44100,astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.Zero_crossings:file=-",
            "-f", "null", "/dev/null"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Parse the output to find the zero crossing rate
        zero_crossings = 0
        zero_crossing_rate = 0  # Initialize the variable before the loop
        for line in result.stderr.split('\n'):
            if "Zero_crossings" in line:
                try:
                    zero_crossings = float(line.split('=')[1].strip())
                    # Convert to a rate (per second)
                    zero_crossing_rate = zero_crossings / 44100
                except (ValueError, IndexError):
                    zero_crossing_rate = 0
        
        # Estimate presence of vocals and music based on these features
        vocal_score = (1 - spectral_flatness) * zero_crossing_rate * 100
        music_score = spectral_flatness * 50
        
        # Normalize to 0-100 scale
        vocal_score = min(100, max(0, vocal_score))
        music_score = min(100, max(0, music_score))
        
        return {
            "vocal_score": round(vocal_score, 2),
            "music_score": round(music_score, 2),
            "spectral_flatness": round(spectral_flatness, 4),
            "zero_crossing_rate": round(zero_crossing_rate, 4),
            "likely_has_music": music_score > 20,
            "likely_has_vocals": vocal_score > 30
        }
        
    except Exception as e:
        logger.error(f"Error analyzing audio: {str(e)}")
        return {
            "error": str(e)
        }

if __name__ == "__main__":
    # Example usage
    input_file = "path/to/input.wav"
    output_dir = "outputs"
    session_id = "test_session"
    
    result = separate_vocals_from_background(input_file, output_dir, session_id)
    print(result)
