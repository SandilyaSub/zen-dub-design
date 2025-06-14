#!/usr/bin/env python3
"""
Configuration module for speech processing settings.
Provides centralized configuration for VAD, diarization, and transcription.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
PYANNOTE_API_KEY = os.getenv("PYANNOTE_API_KEY")

# Default VAD Configuration
DEFAULT_VAD_CONFIG = {
    "enabled": True,
    "threshold": 0.5,
    "combine_duration": 8.0,  # Maximum duration for combined segments in seconds
    "combine_gap": 1.0,       # Maximum gap between segments to combine in seconds
    "sample_rate": 16000,     # Sample rate for audio processing
    "min_segment_duration": 1.0  # Minimum duration for VAD segments in seconds
}

# Default Diarization Configuration
DEFAULT_DIARIZATION_CONFIG = {
    "enabled": True,
    "model": "saarika:v2",    # Sarvam model to use for transcription
    "min_speakers": None,     # Minimum number of speakers (None for auto-detection)
    "max_speakers": None      # Maximum number of speakers (None for auto-detection)
}

# Default Transcription Configuration
DEFAULT_TRANSCRIPTION_CONFIG = {
    "model": "saarika:v2",
    "language": None,         # Language code (None for auto-detection)
    "translate": False,       # Whether to translate the transcription
    "target_language": "en"   # Target language for translation
}

def get_vad_config(override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the VAD configuration with optional overrides.
    
    Args:
        override_config: Dictionary of configuration values to override
        
    Returns:
        Complete VAD configuration
    """
    config = DEFAULT_VAD_CONFIG.copy()
    if override_config:
        config.update(override_config)
    return config

def get_diarization_config(override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the diarization configuration with optional overrides.
    
    Args:
        override_config: Dictionary of configuration values to override
        
    Returns:
        Complete diarization configuration
    """
    config = DEFAULT_DIARIZATION_CONFIG.copy()
    if override_config:
        config.update(override_config)
    return config

def get_transcription_config(override_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Get the transcription configuration with optional overrides.
    
    Args:
        override_config: Dictionary of configuration values to override
        
    Returns:
        Complete transcription configuration
    """
    config = DEFAULT_TRANSCRIPTION_CONFIG.copy()
    if override_config:
        config.update(override_config)
    return config

def get_api_url(translate: bool = False) -> str:
    """
    Get the appropriate Sarvam API URL based on whether translation is required.
    
    Args:
        translate: Whether to use the translation endpoint
        
    Returns:
        API URL
    """
    if translate:
        return "https://api.sarvam.ai/speech-to-text-translate"
    else:
        return "https://api.sarvam.ai/speech-to-text"
