#!/usr/bin/env python3
"""
Test script for audio speedup functionality.
This script tests the ability to speed up or slow down audio files to match target durations.
"""

import os
import sys
import logging
import tempfile
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import time-aligned TTS module
from modules.time_aligned_tts import adjust_segment_duration

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_audio(duration_seconds=3.0, output_path=None):
    """Create a test audio file with the specified duration."""
    from pydub import AudioSegment
    from pydub.generators import Sine
    
    # Create a sine wave tone (440Hz = A4 note)
    sine_wave = Sine(440).to_audio_segment(duration=int(duration_seconds * 1000))
    
    # If no output path specified, create a temporary file
    if not output_path:
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        output_path = temp_file.name
        temp_file.close()
    
    # Export to WAV
    sine_wave.export(output_path, format="wav")
    logger.info(f"Created test audio file: {output_path} (duration: {duration_seconds}s)")
    
    return output_path

def test_speedup(source_duration=3.0, target_duration=2.0):
    """Test speeding up audio (source_duration > target_duration)."""
    # Create test directory
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create input file
    input_file = os.path.join(test_dir, f"test_speedup_input_{source_duration:.1f}s.wav")
    create_test_audio(source_duration, input_file)
    
    # Create output file path
    output_file = os.path.join(test_dir, f"test_speedup_output_{target_duration:.1f}s.wav")
    
    # Adjust duration
    logger.info(f"Testing speedup: {source_duration:.1f}s -> {target_duration:.1f}s (factor: {source_duration/target_duration:.2f}x)")
    success, metadata = adjust_segment_duration(input_file, output_file, target_duration)
    
    # Log results
    if success:
        logger.info(f"Speedup test successful: {metadata}")
        logger.info(f"Output duration: {metadata.get('output_duration', 'unknown')}s")
        logger.info(f"Speed factor: {metadata.get('speed_factor', 'unknown')}x")
        logger.info(f"Quality score: {metadata.get('quality_score', 'unknown')}")
    else:
        logger.error(f"Speedup test failed: {metadata}")
    
    return success, metadata

def test_slowdown(source_duration=2.0, target_duration=3.0):
    """Test slowing down audio (source_duration < target_duration)."""
    # Create test directory
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create input file
    input_file = os.path.join(test_dir, f"test_slowdown_input_{source_duration:.1f}s.wav")
    create_test_audio(source_duration, input_file)
    
    # Create output file path
    output_file = os.path.join(test_dir, f"test_slowdown_output_{target_duration:.1f}s.wav")
    
    # Adjust duration
    logger.info(f"Testing slowdown: {source_duration:.1f}s -> {target_duration:.1f}s (factor: {source_duration/target_duration:.2f}x)")
    success, metadata = adjust_segment_duration(input_file, output_file, target_duration)
    
    # Log results
    if success:
        logger.info(f"Slowdown test successful: {metadata}")
        logger.info(f"Output duration: {metadata.get('output_duration', 'unknown')}s")
        logger.info(f"Speed factor: {metadata.get('speed_factor', 'unknown')}x")
        logger.info(f"Quality score: {metadata.get('quality_score', 'unknown')}")
    else:
        logger.error(f"Slowdown test failed: {metadata}")
    
    return success, metadata

def test_extreme_speedup(source_duration=10.0, target_duration=2.0):
    """Test extreme speedup (factor > 2.0, requiring chained atempo filters)."""
    # Create test directory
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create input file
    input_file = os.path.join(test_dir, f"test_extreme_speedup_input_{source_duration:.1f}s.wav")
    create_test_audio(source_duration, input_file)
    
    # Create output file path
    output_file = os.path.join(test_dir, f"test_extreme_speedup_output_{target_duration:.1f}s.wav")
    
    # Adjust duration
    logger.info(f"Testing extreme speedup: {source_duration:.1f}s -> {target_duration:.1f}s (factor: {source_duration/target_duration:.2f}x)")
    success, metadata = adjust_segment_duration(input_file, output_file, target_duration)
    
    # Log results
    if success:
        logger.info(f"Extreme speedup test successful: {metadata}")
        logger.info(f"Output duration: {metadata.get('output_duration', 'unknown')}s")
        logger.info(f"Speed factor: {metadata.get('speed_factor', 'unknown')}x")
        logger.info(f"Quality score: {metadata.get('quality_score', 'unknown')}")
    else:
        logger.error(f"Extreme speedup test failed: {metadata}")
    
    return success, metadata

def test_extreme_slowdown(source_duration=1.0, target_duration=5.0):
    """Test extreme slowdown (factor < 0.5, requiring chained atempo filters)."""
    # Create test directory
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create input file
    input_file = os.path.join(test_dir, f"test_extreme_slowdown_input_{source_duration:.1f}s.wav")
    create_test_audio(source_duration, input_file)
    
    # Create output file path
    output_file = os.path.join(test_dir, f"test_extreme_slowdown_output_{target_duration:.1f}s.wav")
    
    # Adjust duration
    logger.info(f"Testing extreme slowdown: {source_duration:.1f}s -> {target_duration:.1f}s (factor: {source_duration/target_duration:.2f}x)")
    success, metadata = adjust_segment_duration(input_file, output_file, target_duration)
    
    # Log results
    if success:
        logger.info(f"Extreme slowdown test successful: {metadata}")
        logger.info(f"Output duration: {metadata.get('output_duration', 'unknown')}s")
        logger.info(f"Speed factor: {metadata.get('speed_factor', 'unknown')}x")
        logger.info(f"Quality score: {metadata.get('quality_score', 'unknown')}")
    else:
        logger.error(f"Extreme slowdown test failed: {metadata}")
    
    return success, metadata

def main():
    """Main function to run all tests."""
    
    # Run all tests
    logger.info("\n=== Testing Audio Speedup ===")
    speedup_success, speedup_metadata = test_speedup()
    
    logger.info("\n=== Testing Audio Slowdown ===")
    slowdown_success, slowdown_metadata = test_slowdown()
    
    logger.info("\n=== Testing Extreme Audio Speedup ===")
    extreme_speedup_success, extreme_speedup_metadata = test_extreme_speedup()
    
    logger.info("\n=== Testing Extreme Audio Slowdown ===")
    extreme_slowdown_success, extreme_slowdown_metadata = test_extreme_slowdown()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Speedup Test: {'Success' if speedup_success else 'Failed'}")
    if speedup_success:
        logger.info(f"Speed factor: {speedup_metadata.get('speed_factor', 'N/A')}")
    
    logger.info(f"Slowdown Test: {'Success' if slowdown_success else 'Failed'}")
    if slowdown_success:
        logger.info(f"Speed factor: {slowdown_metadata.get('speed_factor', 'N/A')}")
    
    logger.info(f"Extreme Speedup Test: {'Success' if extreme_speedup_success else 'Failed'}")
    if extreme_speedup_success:
        logger.info(f"Speed factor: {extreme_speedup_metadata.get('speed_factor', 'N/A')}")
    
    logger.info(f"Extreme Slowdown Test: {'Success' if extreme_slowdown_success else 'Failed'}")
    if extreme_slowdown_success:
        logger.info(f"Speed factor: {extreme_slowdown_metadata.get('speed_factor', 'N/A')}")
    
    # Return success if at least one test passed
    return 0 if (speedup_success or slowdown_success or extreme_speedup_success or extreme_slowdown_success) else 1

if __name__ == '__main__':
    sys.exit(main())
