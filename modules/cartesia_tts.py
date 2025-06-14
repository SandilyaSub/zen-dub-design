import os
import logging
import requests
import json

# Import Secret Manager utility
from utils.secret_manager import get_secret

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Available voices
AVAILABLE_VOICES = {
    'nanna': {
        'id': '1982e98c-ab43-4f2c-914f-9741a30a1215',
        'name': "Nanna",
        'gender': 'Male'
    },
    'Madhu': {
        'id': '2bd002c1-209e-48f7-ba51-33901ba577d8',
        'name': "Madhu",
        'gender': 'Male'
    },
    'Budatha': {
        'id': 'd44a6428-287f-494b-864a-cf818d5fa315',
        'name': "Budatha",
        'gender': 'Male'
    },
    'Mahesh': {
        'id': '0be67af6-00c0-4dfe-8ada-8aebd2cb9da4',
        'name': "Mahesh",
        'gender': 'Male'
    },
    'Balli': {
        'id': '999a07d4-9fea-4c91-bdc7-3a383e926a88',
        'name': "Balli",
        'gender': 'Male'
    },
    '1A-Sir': {
        'id': '21861aad-ec85-476d-b6f5-3b072c1737cb',
        'name': "1A-Sir",
        'gender': 'Male'
    },
    'Bunty': {
        'id': 'edc1ff85-2658-451c-8e7c-36fe58e36dd1',
        'name': "Bunty",
        'gender': 'Male'
    },
    'RoshanFriend': {
        'id': 'caeee2ba-7203-4446-831c-b5ecc7c636da',
        'name': "RoshanFriend",
        'gender': 'Male'
    },
    'ClassLeader': {
        'id': 'f779cd6a-fd51-49ff-9984-85303a1142cb',
        'name': "ClassLeader",
        'gender': 'Male'
    },
    'Chorus': {
        'id': '22521244-0921-4759-bf8d-3943efa491de',
        'name': "Chorus",
        'gender': 'Male'
    },
    'Student': {
        'id': '5d68aca2-cf26-4f01-84ce-3b067d0d4adb',
        'name': "Student",
        'gender': 'Male'
    },
    'Saleem': {
        'id': '6c494a79-ebea-46a3-b89e-eeb6bcf9a9d6',
        'name': "Saleem",
        'gender': 'Male'
    },
    'Vaishnavi': {
        'id': '6452a836-cd72-45bc-ab0d-b47b999594dd',
        'name': "Vaishnavi",
        'gender': 'Female'
    },
    'Sandilya': {
        'id': '0c39223f-46e0-4d06-b96b-3c0b332adbf5',
        'name': "Sandilya",
        'gender': 'Male'
    }
}

# Default API version
default_api_version = '2024-11-13'

def get_cartesia_api_key():
    """Get the Cartesia API key from Secret Manager or environment variables."""
    api_key = get_secret("cartesia-api-key")
    if api_key:
        logger.info(f"Cartesia API key is present with length: {len(api_key)}")
        logger.info(f"First 4 chars of API key: {api_key[:4]}")
    else:
        logger.error("Failed to retrieve Cartesia API key")
    return api_key

def get_cartesia_api_version():
    """Get the Cartesia API version from Secret Manager or environment variables."""
    api_version = get_secret("cartesia-api-version")
    if not api_version:
        logger.info(f"Using default Cartesia API version: {default_api_version}")
        api_version = default_api_version
    return api_version

def get_available_voices():
    """
    Get list of available Cartesia voices.
    
    Returns:
        list: List of available voice information
    """
    voices = []
    
    for voice_id, voice_info in AVAILABLE_VOICES.items():
        voice = {
            'id': voice_info['id'],
            'name': voice_info['name'],
            'gender': voice_info['gender']
        }
        voices.append(voice)
    
    return voices

def synthesize_speech(text, output_path, voice_id=None, bit_rate=128000, sample_rate=44100, duration=None):
    """
    Synthesize speech from text using Cartesia API.
    
    Args:
        text: Text to synthesize
        output_path: Path to save the synthesized audio
        voice_id: Voice ID to use (defaults to Dhwani if not specified)
        bit_rate: Audio bit rate
        sample_rate: Audio sample rate
        duration: Desired duration in seconds (not used, kept for backward compatibility)
        
    Returns:
        bool: Success status
    """
    try:
        # Use default voice if none specified
        if not voice_id:
            voice_id = AVAILABLE_VOICES['dhwani']['id']
            logger.info(f"No voice specified, using default voice: {voice_id}")
        
        logger.info(f"Synthesizing speech with Cartesia API using voice: {voice_id}")
        
        # Get API key and version dynamically
        CARTESIA_API_KEY = get_cartesia_api_key()
        CARTESIA_API_VERSION = get_cartesia_api_version()
        
        # Check for API key
        if not CARTESIA_API_KEY:
            logger.error("No Cartesia API key found.")
            return False
        
        # Prepare API request
        url = "https://api.cartesia.ai/tts/bytes"
        headers = {
            "Cartesia-Version": CARTESIA_API_VERSION,
            "X-API-Key": CARTESIA_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "model_id": "sonic-2",
            "transcript": text,
            "voice": {
                "mode": "id",
                "id": voice_id
            },
            "output_format": {
                "container": "mp3",
                "bit_rate": bit_rate,
                "sample_rate": sample_rate
            },
            "language": "hi",  # Hindi is the only language we use Cartesia for
            "speed": "slow"
        }
        
        # Removed duration parameter to ensure consistent time alignment with Sarvam TTS
        # Time alignment will be handled by the time_aligned_tts module instead
        
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Check for successful response
        if response.status_code == 200:
            # Check content type to determine how to handle the response
            content_type = response.headers.get('Content-Type', '')
            
            # If content type is audio, save directly
            if 'audio' in content_type:
                logger.info("Received audio data directly from Cartesia API")
                
                # Save the audio data
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                logger.info(f"Speech synthesis complete: {output_path}")
                return True
            else:
                # Try to parse as JSON (old API behavior)
                try:
                    result = response.json()
                    
                    # Extract audio data
                    audio_base64 = result.get("audio", "")
                    if audio_base64:
                        import base64
                        audio_data = base64.b64decode(audio_base64)
                        
                        # Save the audio data
                        with open(output_path, "wb") as f:
                            f.write(audio_data)
                        
                        logger.info(f"Speech synthesis complete: {output_path}")
                        return True
                    else:
                        logger.error("No audio data received from API")
                        return False
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    return False
        else:
            logger.error(f"API request failed with status code {response.status_code}: {response.text}")
            return False
        
    except Exception as e:
        logger.error(f"Error synthesizing speech with Cartesia: {e}")
        return False
