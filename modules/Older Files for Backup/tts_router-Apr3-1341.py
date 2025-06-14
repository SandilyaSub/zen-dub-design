import os
import logging
from pathlib import Path

# Import TTS modules
from modules.sarvam_tts import synthesize_speech as sarvam_synthesize
from modules.sarvam_tts import get_available_voices as get_sarvam_voices
from modules.cartesia_tts import synthesize_speech as cartesia_synthesize
from modules.cartesia_tts import get_available_voices as get_cartesia_voices
from modules.sarvam_tts import time_aligned_tts_sarvam

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_available_voices(language=None):
    """
    Get list of available voices for a specific language or all languages.
    
    Args:
        language: Language code (optional)
        
    Returns:
        dict: Dictionary of available voices by provider
    """
    voices = {
        "sarvam": [],
        "cartesia": []
    }
    
    # Get Sarvam voices
    sarvam_voices = get_sarvam_voices(language)
    for voice in sarvam_voices:
        voices["sarvam"].append({
            "provider": "sarvam",
            "id": voice["id"],
            "name": voice["name"],
            "gender": voice["gender"]
        })
    
    # Get Cartesia voices (only for Hindi)
    if language is None or language == "hindi":
        cartesia_voices = get_cartesia_voices()
        for voice in cartesia_voices:
            voices["cartesia"].append({
                "provider": "cartesia",
                "id": voice["id"],
                "name": voice["name"],
                "gender": voice["gender"]
            })
    
    return voices

def synthesize_speech(text, language, output_path, voice_id=None, provider='sarvam', options=None, segments=None):
    """
    Synthesize speech using the specified provider.
    
    Args:
        text: Text to synthesize (ignored if segments provided)
        language: Target language
        output_path: Path to save the audio
        voice_id: ID of the voice to use
        provider: TTS provider ('sarvam' or 'cartesia')
        options: Dictionary of provider-specific options
        segments: List of segments to synthesize (if provided, overrides text)
    
    Returns:
        bool: Success status
    """
    try:
        if segments:
            # Use time-aligned synthesis if segments provided
            return time_aligned_tts_sarvam(
                segments=segments,
                output_path=output_path,
                language=language,
                speaker=voice_id,
                options=options
            )
        else:
            # Use regular synthesis if no segments provided
            if provider == 'sarvam':
                return sarvam_synthesize(
                    text=text,
                    language=language,
                    output_path=output_path,
                    speaker=voice_id or "meera",
                    pitch=options.get("pitch", 0),
                    pace=options.get("pace", 1.0),
                    loudness=options.get("loudness", 1.0)
                )
            elif provider == 'cartesia':
                return cartesia_synthesize(
                    text=text,
                    output_path=output_path,
                    voice_id=voice_id,
                    bit_rate=options.get("bit_rate", 128000),
                    sample_rate=options.get("sample_rate", 44100)
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")
                
    except Exception as e:
        logger.error(f"Error in synthesize_speech: {e}")
        return False
