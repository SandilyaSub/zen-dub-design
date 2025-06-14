#!/usr/bin/env python3
"""
OpenAI Text-to-Speech Module
============================

This module provides functions for synthesizing speech using OpenAI's TTS API.
It supports voice mapping from character names to OpenAI voices and instructions.
"""

import os
import json
import requests
import logging
from typing import Dict, Any, Optional
import time
import tempfile
from pydub import AudioSegment

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OPENAI_API_ENDPOINT = "https://api.openai.com/v1/audio/speech"
OPENAI_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "alloy"
VOICE_MAPPING_FILE = os.path.join(os.path.dirname(__file__), "MCMOpenAIVoices.json")
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

def get_openai_api_key() -> Optional[str]:
    """
    Get the OpenAI API key from environment variables.
    
    Returns:
        str: OpenAI API key or None if not found
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY environment variable not found")
        return None
    return api_key

def load_voice_mappings() -> list:
    """
    Load voice mappings from the MCMOpenAIVoices.json file.
    
    Returns:
        list: List of voice mapping dictionaries
    """
    try:
        if not os.path.exists(VOICE_MAPPING_FILE):
            logger.warning(f"Voice mapping file not found: {VOICE_MAPPING_FILE}")
            return []
        
        with open(VOICE_MAPPING_FILE, 'r') as f:
            mappings = json.load(f)
        
        logger.info(f"Loaded {len(mappings)} voice mappings from {VOICE_MAPPING_FILE}")
        return mappings
    except Exception as e:
        logger.error(f"Error loading voice mappings: {e}")
        return []

def map_voice_to_openai(voice_id: str) -> tuple:
    """
    Map a voice ID (character name) to OpenAI voice and instructions.
    
    Args:
        voice_id: The voice ID provided by the user
        
    Returns:
        tuple: (openai_voice, instructions)
    """
    mappings = load_voice_mappings()
    
    # Find the character in the mappings
    for mapping in mappings:
        if mapping["voice"].lower() == voice_id.lower():
            logger.info(f"Mapped voice '{voice_id}' to OpenAI voice '{mapping['openAI_voice']}' with instructions")
            return mapping["openAI_voice"], mapping["instructions"]
    
    # If not found, return a default
    logger.warning(f"Voice '{voice_id}' not found in mappings, using default voice '{DEFAULT_VOICE}'")
    return DEFAULT_VOICE, ""

def synthesize_speech(text: str, voice_id: str, output_path: str, api_key: Optional[str] = None) -> bool:
    """
    Synthesize speech using OpenAI's TTS API.
    
    Args:
        text: The text to synthesize
        voice_id: The voice ID (character name) to use
        output_path: Path to save the synthesized audio
        api_key: OpenAI API key (optional, will use environment variable if not provided)
        
    Returns:
        bool: Success status
    """
    # Get API key
    openai_api_key = api_key or get_openai_api_key()
    if not openai_api_key:
        logger.error("No OpenAI API key available")
        return False
    
    # Map voice ID to OpenAI voice and instructions
    openai_voice, instructions = map_voice_to_openai(voice_id)
    
    # Prepare request
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": OPENAI_MODEL,
        "input": text,
        "voice": openai_voice,
        "response_format": "mp3"
    }
    
    # Add instructions if available
    if instructions:
        payload["instructions"] = instructions
    
    # Make API request with retries
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Sending TTS request to OpenAI (attempt {attempt+1}/{MAX_RETRIES})")
            response = requests.post(OPENAI_API_ENDPOINT, headers=headers, json=payload)
            
            if response.status_code == 200:
                # Save the MP3 to a temporary file first
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_mp3_path = temp_file.name
                
                try:
                    # Convert MP3 to WAV using pydub
                    logger.info(f"Converting MP3 to WAV format")
                    audio = AudioSegment.from_mp3(temp_mp3_path)
                    audio.export(output_path, format="wav")
                    
                    # Remove temporary MP3 file
                    os.remove(temp_mp3_path)
                    
                    logger.info(f"Successfully synthesized speech and saved to {output_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error converting MP3 to WAV: {e}")
                    return False
            else:
                error_msg = f"OpenAI API request failed with status code {response.status_code}: {response.text}"
                logger.error(error_msg)
                
                # Check for rate limiting or server errors
                if response.status_code in [429, 500, 502, 503, 504]:
                    logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    # Other errors are not retryable
                    return False
                
        except Exception as e:
            logger.error(f"Error during OpenAI TTS synthesis: {e}")
            
            # Retry on connection errors
            if attempt < MAX_RETRIES - 1:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                return False
    
    return False
