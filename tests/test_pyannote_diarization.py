#!/usr/bin/env python3
"""
Test script for pyannote.ai diarization API using their recommended approach
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from dotenv import load_dotenv
import uuid

# Load environment variables
load_dotenv()

# Get API token from environment variable
PYANNOTE_API_TOKEN = os.getenv("PYANNOTE_API_TOKEN")

def upload_to_pyannote_storage(file_path):
    """
    Upload the audio file to pyannote.ai temporary storage
    """
    print(f"Uploading file to pyannote.ai storage: {file_path}")
    
    # Generate a unique media identifier
    media_id = f"media://indic-translator/{uuid.uuid4()}.mp3"
    
    # Step 1: Create a pre-signed URL for upload
    create_url = "https://api.pyannote.ai/v1/media/input"
    headers = {
        "Authorization": f"Bearer {PYANNOTE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    body = {
        "url": media_id
    }
    
    try:
        # Create a pre-signed URL
        response = requests.post(create_url, json=body, headers=headers)
        response.raise_for_status()
        data = response.json()
        presigned_url = data.get("url")
        
        if not presigned_url:
            print("Error: No pre-signed URL received")
            return None
        
        print(f"Uploading to pre-signed URL: {presigned_url}")
        
        # Step 2: Upload the file to the pre-signed URL
        with open(file_path, "rb") as input_file:
            upload_response = requests.put(presigned_url, data=input_file)
            upload_response.raise_for_status()
        
        print(f"File uploaded successfully. Media ID: {media_id}")
        return media_id
    
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

def send_diarization_request(media_id, num_speakers=None):
    """
    Send diarization request to pyannote.ai API
    """
    print(f"Sending diarization request for media: {media_id}")
    
    url = "https://api.pyannote.ai/v1/diarize"
    
    payload = {
        "url": media_id,
        "confidence": True
    }
    
    if num_speakers is not None:
        payload["numSpeakers"] = num_speakers
    
    headers = {
        "Authorization": f"Bearer {PYANNOTE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        print("Sending request to API...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error sending request: {e}")
        return None

def check_job_status(job_id):
    """
    Check the status of a diarization job
    """
    url = f"https://api.pyannote.ai/v1/jobs/{job_id}"
    
    headers = {
        "Authorization": f"Bearer {PYANNOTE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to check job status: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error checking job status: {e}")
        return None

def get_job_results(job_id):
    """
    Get the results of a completed diarization job
    """
    url = f"https://api.pyannote.ai/v1/jobs/{job_id}/results"
    
    headers = {
        "Authorization": f"Bearer {PYANNOTE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to get job results: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting job results: {e}")
        return None

def format_diarization_output(diarization_result):
    """
    Format the diarization result to match the desired output format
    """
    if not diarization_result:
        return None
    
    # Extract segments from the result
    segments = []
    speakers = {}
    
    # Check if the result contains segments directly
    if "segments" in diarization_result:
        raw_segments = diarization_result.get("segments", [])
    # Or if it's nested under a 'diarization' key
    elif "diarization" in diarization_result and "segments" in diarization_result["diarization"]:
        raw_segments = diarization_result["diarization"].get("segments", [])
    else:
        print("Warning: Could not find segments in the result")
        raw_segments = []
    
    for i, segment in enumerate(raw_segments):
        speaker_id = f"spk_{str(segment.get('speaker', '')).zfill(3)}"
        
        formatted_segment = {
            "segment_id": f"seg_{str(i+1).zfill(3)}",
            "speaker_id": speaker_id,
            "start_time": segment.get('start'),
            "end_time": segment.get('end'),
            "text": segment.get('text', ''),
            "confidence": segment.get('confidence', 0.95)
        }
        
        segments.append(formatted_segment)
        
        # Add speaker to speakers dict if not already there
        if speaker_id not in speakers:
            speakers[speaker_id] = {
                "sex": "unknown"
            }
    
    return {
        "segments": segments,
        "speakers": speakers
    }

def save_results(result, formatted_result, output_dir):
    """
    Save the raw and formatted results to files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save raw result
    raw_output_path = os.path.join(output_dir, f"pyannote_raw_{timestamp}.json")
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Raw result saved to: {raw_output_path}")
    
    # Save formatted result
    if formatted_result:
        formatted_output_path = os.path.join(output_dir, f"pyannote_formatted_{timestamp}.json")
        with open(formatted_output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_result, f, indent=2, ensure_ascii=False)
        
        print(f"Formatted result saved to: {formatted_output_path}")

def main():
    parser = argparse.ArgumentParser(description="Test pyannote.ai diarization API")
    parser.add_argument("audio_file", help="Path to the audio file")
    parser.add_argument("--num-speakers", type=int, help="Number of speakers (optional)")
    parser.add_argument("--output-dir", default="test_outputs", help="Directory to save results")
    parser.add_argument("--max-wait", type=int, default=300, help="Maximum wait time in seconds (default: 300)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.audio_file):
        print(f"Error: Audio file not found: {args.audio_file}")
        return 1
    
    if not PYANNOTE_API_TOKEN:
        print("Error: PYANNOTE_API_TOKEN environment variable not set")
        print("Please set it in your .env file or environment variables")
        return 1
    
    print(f"Testing pyannote.ai diarization API with file: {args.audio_file}")
    print(f"Number of speakers: {args.num_speakers if args.num_speakers else 'auto'}")
    
    # Step 1: Upload file to pyannote.ai storage
    media_id = upload_to_pyannote_storage(args.audio_file)
    
    if not media_id:
        print("Error: Failed to upload file to pyannote.ai storage")
        return 1
    
    # Step 2: Send diarization request
    job_response = send_diarization_request(media_id, args.num_speakers)
    
    if not job_response:
        print("Error: Diarization request failed")
        return 1
    
    # Save the initial job response
    os.makedirs(args.output_dir, exist_ok=True)
    initial_response_path = os.path.join(args.output_dir, "initial_job_response.json")
    with open(initial_response_path, 'w', encoding='utf-8') as f:
        json.dump(job_response, f, indent=2, ensure_ascii=False)
    
    print(f"Initial job response saved to: {initial_response_path}")
    
    # Extract job ID
    job_id = job_response.get("jobId")
    if not job_id:
        print("Error: No job ID found in response")
        return 1
    
    print(f"Diarization job created with ID: {job_id}")
    print(f"Waiting for job to complete (max {args.max_wait} seconds)...")
    
    # Step 3: Poll for job completion
    start_time = time.time()
    result = None
    
    while time.time() - start_time < args.max_wait:
        # Check job status
        status_response = check_job_status(job_id)
        
        if not status_response:
            print("Error checking job status")
            time.sleep(5)
            continue
        
        job_status = status_response.get("status")
        print(f"Current job status: {job_status}")
        
        if job_status == "completed":
            # Job is complete, get results
            result = get_job_results(job_id)
            break
        elif job_status in ["failed", "canceled"]:
            print(f"Job {job_status}: {status_response.get('error', 'No error message')}")
            return 1
        
        # Wait before checking again
        print("Waiting 5 seconds before checking again...")
        time.sleep(5)
    
    if not result:
        print(f"Timed out waiting for job to complete after {args.max_wait} seconds")
        return 1
    
    # Format the result
    formatted_result = format_diarization_output(result)
    
    # Save results
    save_results(result, formatted_result, args.output_dir)
    
    # Print a summary
    print("\nDiarization Summary:")
    if formatted_result:
        print(f"Total segments: {len(formatted_result.get('segments', []))}")
        print(f"Total speakers: {len(formatted_result.get('speakers', {}))}")
    else:
        print("No formatted results available")
    
    print("\nDone!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
