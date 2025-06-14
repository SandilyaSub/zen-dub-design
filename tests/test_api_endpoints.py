#!/usr/bin/env python3
"""
Test script for diarization API endpoints.
This script tests the API endpoints for getting and saving diarization data.
"""

import os
import json
import requests
import sys
import shutil
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_SESSION_ID = f"test_session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
TEST_DATA_DIR = os.path.join("outputs", TEST_SESSION_ID)

def setup_test_environment():
    """Create test session directory and sample diarization data."""
    print(f"Setting up test environment with session ID: {TEST_SESSION_ID}")
    
    # Create test session directory
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    # Create sample diarization data
    sample_data = {
        "transcript": "हेलो मैं यूलू से अर्पिता बात कर रही हूँ। मैंने देखा कि आपने रेंटल प्लान नहीं खरीदा।",
        "segments": [
            {
                "segment_id": "seg_000",
                "speaker": "SPEAKER_00",
                "text": "हेलो मैं यूलू से अर्पिता बात कर रही हूँ।",
                "start_time": 0.522,
                "end_time": 3.512,
                "gender": "unknown",
                "pace": 1.0
            },
            {
                "segment_id": "seg_001",
                "speaker": "SPEAKER_01",
                "text": "मैंने देखा कि आपने रेंटल प्लान नहीं खरीदा।",
                "start_time": 3.826,
                "end_time": 6.725,
                "gender": "unknown",
                "pace": 1.0
            }
        ],
        "language_code": "hi-IN"
    }
    
    # Save sample data
    with open(os.path.join(TEST_DATA_DIR, "diarization.json"), "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"Created test diarization data at {os.path.join(TEST_DATA_DIR, 'diarization.json')}")
    return sample_data

def test_get_diarization():
    """Test the /api/get_diarization endpoint."""
    print("\n=== Testing GET /api/get_diarization ===")
    
    # Make request
    response = requests.get(f"{BASE_URL}/api/get_diarization", params={"session_id": TEST_SESSION_ID})
    
    # Check response
    if response.status_code == 200:
        data = response.json()
        print("✅ GET /api/get_diarization succeeded")
        print(f"Received {len(data.get('segments', []))} segments")
        return data
    else:
        print(f"❌ GET /api/get_diarization failed with status {response.status_code}")
        print(f"Error: {response.text}")
        return None

def test_save_diarization(original_data):
    """Test the /api/api_save_diarization endpoint."""
    print("\n=== Testing POST /api/api_save_diarization ===")
    
    # Create updates
    updates = {}
    for segment in original_data["segments"]:
        # Modify speaker and text
        updates[segment["segment_id"]] = {
            "speaker": "SPEAKER_02" if segment["speaker"] == "SPEAKER_00" else "SPEAKER_00",
            "text": segment["text"] + " (edited)"
        }
    
    # Make request
    response = requests.post(
        f"{BASE_URL}/api/api_save_diarization",
        json={
            "session_id": TEST_SESSION_ID,
            "updates": updates
        }
    )
    
    # Check response
    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print("✅ POST /api/api_save_diarization succeeded")
            
            # Verify changes were saved
            with open(os.path.join(TEST_DATA_DIR, "diarization.json"), "r", encoding="utf-8") as f:
                updated_data = json.load(f)
            
            all_changes_applied = True
            for segment in updated_data["segments"]:
                seg_id = segment["segment_id"]
                if seg_id in updates:
                    if segment["speaker"] != updates[seg_id]["speaker"] or segment["text"] != updates[seg_id]["text"]:
                        all_changes_applied = False
                        print(f"❌ Changes for segment {seg_id} were not applied correctly")
            
            if all_changes_applied:
                print("✅ All changes were applied correctly")
            
            return updated_data
        else:
            print(f"❌ POST /api/api_save_diarization failed: {result.get('error', 'Unknown error')}")
            return None
    else:
        print(f"❌ POST /api/api_save_diarization failed with status {response.status_code}")
        print(f"Error: {response.text}")
        return None

def cleanup():
    """Clean up test environment."""
    print("\n=== Cleaning up test environment ===")
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
        print(f"✅ Removed test directory: {TEST_DATA_DIR}")

def main():
    """Run the tests."""
    try:
        # Check if server is running
        try:
            response = requests.get(f"{BASE_URL}/")
            if response.status_code != 200:
                print(f"❌ Server at {BASE_URL} is not responding correctly")
                return False
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to server at {BASE_URL}. Make sure the Flask server is running.")
            return False
        
        # Setup test environment
        original_data = setup_test_environment()
        
        # Test get_diarization
        fetched_data = test_get_diarization()
        if not fetched_data:
            return False
        
        # Test save_diarization
        updated_data = test_save_diarization(original_data)
        if not updated_data:
            return False
        
        # Test get_diarization again to verify changes
        fetched_data_after_update = test_get_diarization()
        if not fetched_data_after_update:
            return False
        
        print("\n=== All tests completed successfully ===")
        return True
    
    finally:
        # Always clean up
        cleanup()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
