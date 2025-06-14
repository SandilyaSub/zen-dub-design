#!/usr/bin/env python3
"""
Test script for the time-aligned TTS algorithm logic.
This script tests the core algorithm logic without making actual API calls.
"""

import os
import sys
import json
import logging
from pathlib import Path
from pydub import AudioSegment

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_audio(duration_ms, output_path):
    """Create a test audio file with the specified duration."""
    # Create a silent audio segment
    audio = AudioSegment.silent(duration=duration_ms)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Export audio to file
    try:
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        logger.error(f"Error creating test audio: {e}")
        return False

def test_algorithm_logic():
    """Test the core algorithm logic for time-aligned TTS."""
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Test cases for different duration ratios
    test_cases = [
        {
            "name": "ratio_1.0",
            "input_duration": 5000,  # 5 seconds
            "output_duration": 5000,  # 5 seconds (ratio = 1.0)
            "expected_result": "use_as_is"
        },
        {
            "name": "ratio_0.92",
            "input_duration": 5000,  # 5 seconds
            "output_duration": 4600,  # 4.6 seconds (ratio = 0.92)
            "expected_result": "adjust_pace"
        },
        {
            "name": "ratio_1.08",
            "input_duration": 5000,  # 5 seconds
            "output_duration": 5400,  # 5.4 seconds (ratio = 1.08)
            "expected_result": "adjust_pace"
        },
        {
            "name": "ratio_0.85",
            "input_duration": 5000,  # 5 seconds
            "output_duration": 4250,  # 4.25 seconds (ratio = 0.85)
            "expected_result": "adjust_pace_and_add_silence"
        },
        {
            "name": "ratio_1.15",
            "input_duration": 5000,  # 5 seconds
            "output_duration": 5750,  # 5.75 seconds (ratio = 1.15)
            "expected_result": "check_for_pauses_or_adjust_pace"
        }
    ]
    
    # Run tests
    results = []
    for test_case in test_cases:
        logger.info(f"Testing case: {test_case['name']}")
        
        # Calculate ratio
        ratio = test_case["output_duration"] / test_case["input_duration"]
        logger.info(f"Duration ratio: {ratio:.2f}")
        
        # Determine expected action based on our algorithm
        if 0.95 <= ratio <= 1.05:
            action = "use_as_is"
        elif (0.9 <= ratio < 0.95) or (1.05 < ratio <= 1.1):
            action = "adjust_pace"
        elif ratio > 1.1:
            action = "check_for_pauses_or_adjust_pace"
        else:  # ratio < 0.9
            action = "adjust_pace_and_add_silence"
        
        # Check if the action matches the expected result
        success = (action == test_case["expected_result"])
        
        # Create test audio files to demonstrate
        input_path = os.path.join(output_dir, f"{test_case['name']}_input.wav")
        output_path = os.path.join(output_dir, f"{test_case['name']}_output.wav")
        
        create_test_audio(test_case["input_duration"], input_path)
        create_test_audio(test_case["output_duration"], output_path)
        
        # Record result
        results.append({
            "test_case": test_case["name"],
            "ratio": ratio,
            "expected_action": test_case["expected_result"],
            "actual_action": action,
            "success": success,
            "input_path": input_path,
            "output_path": output_path
        })
    
    # Print results
    logger.info("\n--- Test Results ---")
    all_success = True
    for result in results:
        status = "PASS" if result["success"] else "FAIL"
        logger.info(f"{result['test_case']} ({result['ratio']:.2f}): {status}")
        if not result["success"]:
            all_success = False
            logger.error(f"  Expected: {result['expected_action']}, Got: {result['actual_action']}")
    
    return all_success

def test_segment_merging():
    """Test the logic for merging audio segments with correct timing."""
    
    # Create output directory
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Create test segments
    segments = [
        {"start_time": 1.0, "end_time": 3.0, "duration": 2.0},
        {"start_time": 4.0, "end_time": 5.5, "duration": 1.5},
        {"start_time": 7.0, "end_time": 9.0, "duration": 2.0}
    ]
    
    # Create audio segments
    audio_files = []
    for i, segment in enumerate(segments):
        # Create a silent audio segment for the segment duration
        segment_path = os.path.join(output_dir, f"segment_{i}.wav")
        create_test_audio(int(segment["duration"] * 1000), segment_path)
        audio_files.append(segment_path)
    
    # Merge segments
    merged_audio = AudioSegment.silent(duration=0)
    current_position = 0  # in milliseconds
    
    for i, segment in enumerate(segments):
        # Calculate start time in milliseconds
        start_time_ms = int(segment["start_time"] * 1000)
        
        # Add silence if needed
        if start_time_ms > current_position:
            silence_duration = start_time_ms - current_position
            silence = AudioSegment.silent(duration=silence_duration)
            merged_audio += silence
            logger.info(f"Added {silence_duration}ms silence before segment {i}")
        
        # Load segment audio
        try:
            segment_audio = AudioSegment.from_file(audio_files[i])
            
            # Add segment to merged audio
            merged_audio += segment_audio
            
            # Update current position
            current_position = start_time_ms + len(segment_audio)
            logger.info(f"Added segment {i} at position {start_time_ms}ms, new position: {current_position}ms")
        except Exception as e:
            logger.error(f"Error loading segment {i}: {e}")
            return False
    
    # Export merged audio
    merged_path = os.path.join(output_dir, "merged_segments.wav")
    try:
        merged_audio.export(merged_path, format="wav")
        logger.info(f"Successfully merged segments to {merged_path}")
        
        # Verify merged audio duration
        expected_duration = segments[-1]["end_time"] * 1000  # in milliseconds
        actual_duration = len(merged_audio)
        logger.info(f"Expected duration: {expected_duration}ms, Actual duration: {actual_duration}ms")
        
        # Allow for small differences due to encoding/decoding
        duration_diff = abs(expected_duration - actual_duration)
        success = duration_diff <= 100  # Allow 100ms difference
        
        if success:
            logger.info("Segment merging test PASSED")
        else:
            logger.error(f"Segment merging test FAILED: Duration difference: {duration_diff}ms")
        
        return success
    except Exception as e:
        logger.error(f"Error exporting merged audio: {e}")
        return False

def main():
    """Main function to run the tests."""
    
    # Test algorithm logic
    logger.info("Testing algorithm logic...")
    algorithm_success = test_algorithm_logic()
    
    # Test segment merging
    logger.info("\nTesting segment merging...")
    merging_success = test_segment_merging()
    
    # Print overall results
    logger.info("\n--- Overall Results ---")
    logger.info(f"Algorithm Logic Test: {'PASS' if algorithm_success else 'FAIL'}")
    logger.info(f"Segment Merging Test: {'PASS' if merging_success else 'FAIL'}")
    
    return 0 if algorithm_success and merging_success else 1

if __name__ == '__main__':
    sys.exit(main())
