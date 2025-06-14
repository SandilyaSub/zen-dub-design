import os
import logging
import requests
import json
import base64

# Import Secret Manager utility
from utils.secret_manager import get_secret

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Language code mapping
LANGUAGE_MAP = {
    'hindi': 'hi-IN',
    'english': 'en-IN',
    'telugu': 'te-IN',
    'tamil': 'ta-IN',
    'kannada': 'kn-IN',
    'gujarati': 'gu-IN',
    'marathi': 'mr-IN',
    'bengali': 'bn-IN',
    'odia': 'od-IN',
    'punjabi': 'pa-IN',
    'malayalam': 'ml-IN'
}

# Available speakers by model
AVAILABLE_SPEAKERS = {
    # Speakers for bulbul:v2 model (current default)
    'bulbul:v2': {
        'anushka': {'gender': 'Female', 'name': 'Anushka'},
        'abhilash': {'gender': 'Male', 'name': 'Abhilash'},
        'manisha': {'gender': 'Female', 'name': 'Manisha'},
        'vidya': {'gender': 'Female', 'name': 'Vidya'},
        'arya': {'gender': 'Female', 'name': 'Arya'},
        'karun': {'gender': 'Male', 'name': 'Karun'},
        'hitesh': {'gender': 'Male', 'name': 'Hitesh'}
    },
    # Legacy speakers (for older models)
    'legacy': {
        'meera': {'gender': 'Female', 'name': 'Meera'},
        'pavithra': {'gender': 'Female', 'name': 'Pavithra'},
        'arvind': {'gender': 'Male', 'name': 'Arvind'},
        'amol': {'gender': 'Male', 'name': 'Amol'}
    }
}

# Default model to use
DEFAULT_MODEL = "bulbul:v2"

# Get Sarvam API key from Secret Manager or environment
def get_sarvam_api_key():
    """Get the Sarvam API key from Secret Manager or environment variables."""
    api_key = get_secret("sarvam-api-key")
    if api_key:
        logger.info(f"Sarvam TTS API key is present with length: {len(api_key)}")
        logger.info(f"First 4 chars of API key: {api_key[:4]}")
    else:
        logger.error("Failed to retrieve Sarvam TTS API key")
    return api_key

def get_available_voices(language=None, model=DEFAULT_MODEL):
    """
    Get list of available voices for a specific language or all languages.
    
    Args:
        language: Language code (optional)
        model: TTS model to use (optional)
        
    Returns:
        list: List of available voice information
    """
    voices = []
    
    # Get speakers for the specified model
    speakers = AVAILABLE_SPEAKERS.get(model, AVAILABLE_SPEAKERS['bulbul:v2'])
    
    for voice_id, voice_info in speakers.items():
        voice = {
            'id': voice_id,
            'name': voice_info['name'],
            'gender': voice_info['gender']
        }
        voices.append(voice)
    
    return voices

def synthesize_speech(text, language, output_path, speaker=None, pitch=0, pace=1.0, loudness=1.0, model=DEFAULT_MODEL):
    """
    Synthesize speech from text using Sarvam API.
    
    Args:
        text: Text to synthesize
        language: Target language
        output_path: Path to save the synthesized audio
        speaker: Speaker voice to use (if None, will use first available for the model)
        pitch: Voice pitch adjustment (-0.75 to 0.75)
        pace: Speech speed (0.5 to 2.0)
        loudness: Audio loudness (0.3 to 3.0)
        model: TTS model to use
        
    Returns:
        bool: Success status
    """
    try:
        # Get available speakers for the model
        model_speakers = AVAILABLE_SPEAKERS.get(model, AVAILABLE_SPEAKERS['bulbul:v2'])
        
        # If no speaker specified or speaker not available for this model, use first available
        if not speaker or speaker not in model_speakers:
            if speaker:
                logger.warning(f"Speaker '{speaker}' not compatible with model {model}.")
            
            # Use first available speaker for this model
            speaker = next(iter(model_speakers.keys()))
            logger.info(f"Using speaker '{speaker}' for model {model}")
        
        logger.info(f"Synthesizing speech in {language} with speaker {speaker} using model {model}")
        
        # Get Sarvam API key
        SARVAM_API_KEY = get_sarvam_api_key()
        
        # Check for API key
        if not SARVAM_API_KEY:
            logger.error("No Sarvam API key found.")
            return False
        
        # Convert language name to code if needed
        language_code = LANGUAGE_MAP.get(language, language)
        
        # Prepare API request
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "API-Subscription-Key": SARVAM_API_KEY,
            "Content-Type": "application/json"
        }
        
        # Ensure text is not too long (Sarvam has a 500 character limit per input)
        # Split into chunks if necessary
        text_chunks = []
        max_chunk_size = 500
        
        if len(text) <= max_chunk_size:
            text_chunks = [text]
        else:
            # Split by sentences to avoid cutting in the middle of a sentence
            sentences = text.split('. ')
            current_chunk = ""
            
            for sentence in sentences:
                # Add period back if it was removed during split
                if not sentence.endswith('.'):
                    sentence += '.'
                
                # If adding this sentence would exceed the limit, start a new chunk
                if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                    text_chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += ' ' + sentence
                    else:
                        current_chunk = sentence
            
            # Add the last chunk if it's not empty
            if current_chunk:
                text_chunks.append(current_chunk)
        
        # Process each chunk
        all_audio_data = bytearray()
        
        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processing chunk {i+1}/{len(text_chunks)}")
            
            payload = {
                "inputs": [chunk],
                "target_language_code": language_code,
                "speaker": speaker,
                "pitch": pitch,
                "pace": pace,
                "loudness": loudness,
                "speech_sample_rate": 22050,  # Highest quality
                "enable_preprocessing": True,
                "model": model
            }
            
            # Make API request
            response = requests.post(url, headers=headers, json=payload)
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                
                # Extract audio data
                audio_base64 = result.get("audios", [""])[0]
                if audio_base64:
                    audio_data = base64.b64decode(audio_base64)
                    all_audio_data.extend(audio_data)
                else:
                    logger.error("No audio data received from API")
                    return False
            else:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return False
        
        # Save the combined audio data
        with open(output_path, "wb") as f:
            f.write(all_audio_data)
        
        logger.info(f"Speech synthesis complete: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        return False
