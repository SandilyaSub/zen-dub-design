#!/usr/bin/env python3
"""
Test script for the time-aligned TTS endpoint.
This script sends a POST request to the /api/synthesize-time-aligned endpoint.
"""

import os
import sys
import json
import requests
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_time_aligned_endpoint(session_id, target_language, provider, voice_id=None):
    """Test the time-aligned TTS endpoint with a POST request."""
    
    # API endpoint URL
    url = "http://localhost:5000/api/synthesize-time-aligned"
    
    # Request payload
    payload = {
        "session_id": session_id,
        "target_language": target_language,
        "provider": provider,
        "options": {
            "bit_rate": 128000,
            "sample_rate": 44100
        }
    }
    
    # Add voice_id if specified
    if voice_id:
        payload["voice_id"] = voice_id
    
    logger.info(f"Sending POST request to {url}")
    logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Send POST request
    try:
        response = requests.post(url, json=payload)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Request successful: {json.dumps(result, indent=2)}")
            
            if result.get("success"):
                logger.info(f"Audio URL: {result.get('audio_url')}")
                return True
            else:
                logger.error(f"API error: {result.get('error')}")
                return False
        else:
            logger.error(f"Request failed with status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Error sending request: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Test the time-aligned TTS endpoint')
    parser.add_argument('--session', required=True, help='Session ID')
    parser.add_argument('--language', default='english', help='Target language (e.g., hindi, english, telugu)')
    parser.add_argument('--provider', default='sarvam', choices=['sarvam', 'cartesia'], help='TTS provider to use')
    parser.add_argument('--voice', help='Voice ID to use')
    
    args = parser.parse_args()
    
    # Test the endpoint
    success = test_time_aligned_endpoint(
        session_id=args.session,
        target_language=args.language,
        provider=args.provider,
        voice_id=args.voice
    )
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
