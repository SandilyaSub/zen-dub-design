import os
import torch
import logging
import numpy as np
import soundfile as sf
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Language code mapping
LANGUAGE_MAP = {
    'hindi': 'hi',
    'english': 'en',
    'telugu': 'te',
    'tamil': 'ta',
    'kannada': 'kn',
    'gujarati': 'gu',
    'marathi': 'mr',
    'bengali': 'bn'
}

# Global variables for models
hf_tts_model = None
hf_processor = None

def _load_hf_tts_model():
    """Load the Hugging Face TTS model if not already loaded."""
    global hf_tts_model, hf_processor
    
    if hf_tts_model is not None and hf_processor is not None:
        return hf_tts_model, hf_processor
    
    try:
        logger.info("Loading Hugging Face TTS model...")
        
        # Import here to avoid loading all dependencies at module import time
        from transformers import AutoProcessor, AutoModel
        
        # Initialize TTS model - using Facebook's MMS-TTS model
        model_name = "facebook/mms-tts-eng"  # English model as default
        hf_processor = AutoProcessor.from_pretrained(model_name)
        hf_tts_model = AutoModel.from_pretrained(model_name)
        
        logger.info("Loaded Hugging Face TTS model")
        return hf_tts_model, hf_processor
        
    except Exception as e:
        logger.error(f"Error loading Hugging Face TTS model: {e}")
        return None, None

def _synthesize_with_hf(text, language, output_path):
    """Synthesize speech using Hugging Face's TTS models."""
    try:
        # Load model and processor
        model, processor = _load_hf_tts_model()
        if model is None or processor is None:
            logger.error("Failed to load Hugging Face TTS model")
            return False
        
        # Get language code
        lang_code = LANGUAGE_MAP.get(language, language)
        
        # Process text input
        inputs = processor(text=text, return_tensors="pt")
        
        # Generate speech
        with torch.no_grad():
            output = model(**inputs)
        
        # Save the audio
        sampling_rate = processor.sampling_rate
        sf.write(output_path, output.audio.numpy().squeeze(), sampling_rate)
        
        logger.info(f"Speech synthesized with Hugging Face and saved to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error synthesizing speech with Hugging Face: {e}")
        return False

def _synthesize_with_gtts(text, language, output_path):
    """Synthesize speech using Google Text-to-Speech (gTTS) as a fallback."""
    try:
        from gtts import gTTS
        
        # Get language code
        lang_code = LANGUAGE_MAP.get(language, language)
        
        # Create gTTS object
        tts = gTTS(text=text, lang=lang_code, slow=False)
        
        # Save to file
        tts.save(output_path)
        
        logger.info(f"Speech synthesized with gTTS and saved to {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error synthesizing speech with gTTS: {e}")
        return False

def synthesize_speech(text, language, output_path, reference_audio=None, num_speakers=1, speaker_genders=None):
    """
    Synthesize speech from text using available TTS methods.
    
    Args:
        text: Text to synthesize
        language: Target language
        output_path: Path to save the synthesized audio
        reference_audio: Path to reference audio for voice cloning (not used in this implementation)
        num_speakers: Number of speakers in the audio (not used in this implementation)
        speaker_genders: List of speaker genders (M/F) (not used in this implementation)
        
    Returns:
        success: True if synthesis was successful, False otherwise
    """
    try:
        logger.info(f"Synthesizing speech in {language}")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Try Hugging Face TTS first
        if _synthesize_with_hf(text, language, output_path):
            return True
        
        # If Hugging Face fails, try gTTS as fallback
        logger.info("Falling back to gTTS for speech synthesis")
        if _synthesize_with_gtts(text, language, output_path):
            return True
        
        # If all methods fail
        logger.error("All TTS methods failed")
        return False
        
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        return False
