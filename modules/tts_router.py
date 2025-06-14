import os
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json

# Import TTS modules
from modules.tts_processor import TTSProcessor
from modules.sarvam_tts import get_available_voices as get_sarvam_voices
from modules.cartesia_tts import get_available_voices as get_cartesia_voices

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_available_voices(language: Optional[str] = None) -> Dict:
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

def synthesize_speech(
    text: str,
    language: str,
    output_path: str,
    voice_id: Optional[str] = None,
    provider: str = 'sarvam',
    options: Optional[Dict] = None,
    segments: Optional[List[Dict]] = None
) -> str:
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
        str: Path to the synthesized audio file
    """
    try:
        # Parse session_id from output_path
        if not options:
            options = {}
            
        # Extract session_id properly
        if 'session_' in output_path:
            # Extract session_id from path containing 'session_'
            parts = output_path.split('session_')
            if len(parts) > 1:
                session_id = parts[1].split('/')[0].split('.')[0]  # Remove file extension if present
            else:
                session_id = os.path.splitext(os.path.basename(output_path))[0]
        else:
            session_id = os.path.splitext(os.path.basename(output_path))[0]
        
        # Use the correct session directory structure
        session_dir = os.path.join('outputs', f"session_{session_id}")
        os.makedirs(session_dir, exist_ok=True)
        
        # Ensure TTS directory exists
        tts_dir = os.path.join(session_dir, "tts")
        os.makedirs(tts_dir, exist_ok=True)
        
        # Ensure synthesis directory exists
        synthesis_dir = os.path.join(session_dir, "synthesis")
        os.makedirs(synthesis_dir, exist_ok=True)
        
        # Initialize TTSProcessor
        processor = TTSProcessor(
            session_id=session_id,
            output_dir=session_dir
        )
        
        # Set provider details in the logger
        processor.logger.set_provider_details(
            provider=provider,
            language=language,
            speaker=voice_id or "anushka",
            model=options.get("model", "bulbul:v2")
        )
        
        # If segments provided, use them directly
        if segments:
            # Add language to each segment
            for segment in segments:
                segment['language'] = language
                
            # Save segments to a temporary JSON file in the synthesis directory
            segments_file = os.path.join(synthesis_dir, "segments.json")
            with open(segments_file, 'w', encoding='utf-8') as f:
                json.dump(segments, f, ensure_ascii=False, indent=2)
            
            # Process segments
            audio_path = processor.process_tts(segments_file)
            
        else:
            # Create single segment from text
            segments = [{
                "segment_id": "0",
                "speaker": "SPEAKER_00",
                "start_time": 0.0,
                "end_time": 0.0,  # Will be updated by TTSProcessor
                "duration": 0.0,  # Will be updated by TTSProcessor
                "text": text,
                "translated_text": text,
                "gender": "M",
                "language": language  # Add language to the segment
            }]
            
            # Save single segment to temporary JSON in the synthesis directory
            segments_file = os.path.join(synthesis_dir, "single_segment.json")
            with open(segments_file, 'w', encoding='utf-8') as f:
                json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
            
            # Process single segment
            audio_path = processor.process_tts(segments_file)
            
        # Copy final output to requested output path
        final_output = os.path.join(tts_dir, os.path.basename(audio_path))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        os.rename(final_output, output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error in TTS synthesis: {str(e)}")
        raise
