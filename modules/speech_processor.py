#!/usr/bin/env python3
"""
Comprehensive speech processing module that integrates VAD segmentation, 
diarization, transcription, and translation capabilities.
"""

import os
import json
import logging
import asyncio
import tempfile
from typing import Dict, Any, Optional, List, Union
from . import vad_segmentation
from . import sarvam_speech
from . import speech_config

# Configure logging
logger = logging.getLogger(__name__)

class SpeechProcessor:
    """
    Unified speech processing class that handles the complete pipeline from
    audio input to transcription with diarization and optional translation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the speech processor.
        
        Args:
            api_key: Sarvam API key (if None, will use from environment)
        """
        self.api_key = api_key or speech_config.SARVAM_API_KEY
        if not self.api_key:
            raise ValueError("Sarvam API key is required. Set it in .env file or pass it to the constructor.")
        
        # Load default configurations
        self.vad_config = speech_config.get_vad_config()
        self.diarization_config = speech_config.get_diarization_config()
        self.transcription_config = speech_config.get_transcription_config()
        
        logger.info("Speech processor initialized")
    
    def configure(self, 
                  vad_config: Optional[Dict[str, Any]] = None,
                  diarization_config: Optional[Dict[str, Any]] = None,
                  transcription_config: Optional[Dict[str, Any]] = None):
        """
        Configure the speech processor with custom settings.
        
        Args:
            vad_config: VAD configuration overrides
            diarization_config: Diarization configuration overrides
            transcription_config: Transcription configuration overrides
        """
        if vad_config:
            self.vad_config.update(vad_config)
            logger.info(f"Updated VAD configuration: {self.vad_config}")
        
        if diarization_config:
            self.diarization_config.update(diarization_config)
            logger.info(f"Updated diarization configuration: {self.diarization_config}")
        
        if transcription_config:
            self.transcription_config.update(transcription_config)
            logger.info(f"Updated transcription configuration: {self.transcription_config}")
    
    async def process_audio(self, 
                           audio_path: str, 
                           output_dir: Optional[str] = None,
                           save_results: bool = True) -> Dict[str, Any]:
        """
        Process an audio file with the configured settings.
        
        Args:
            audio_path: Path to the audio file
            output_dir: Directory to save results and temporary files
            save_results: Whether to save results to disk
            
        Returns:
            Dictionary containing processing results
        """
        logger.info(f"Processing audio: {audio_path}")
        
        # Create output directory if needed
        if save_results and output_dir:
            os.makedirs(output_dir, exist_ok=True)
            temp_dir = os.path.join(output_dir, "segments")
        else:
            temp_dir = tempfile.mkdtemp(prefix="speech_processor_")
        
        # Process with VAD and diarization
        try:
            results = await sarvam_speech.transcribe_with_vad_diarization(
                audio_path=audio_path,
                api_key=self.api_key,
                use_vad=self.vad_config["enabled"],
                vad_threshold=self.vad_config["threshold"],
                combine_duration=self.vad_config["combine_duration"],
                combine_gap=self.vad_config["combine_gap"],
                temp_dir=temp_dir
            )
            
            # Save results if requested
            if save_results and output_dir:
                results_path = os.path.join(output_dir, "speech_results.json")
                with open(results_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                logger.info(f"Results saved to: {results_path}")
            
            # Format results for application use
            formatted_results = self._format_results(results)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the processing results for application use.
        
        Args:
            results: Raw processing results
            
        Returns:
            Formatted results
        """
        # Extract speakers from segments
        speakers = {}
        for segment in results.get("segments", []):
            speaker_id = segment.get("speaker", "unknown")
            if speaker_id not in speakers:
                speakers[speaker_id] = {
                    "id": speaker_id,
                    "gender": "unknown"  # We don't have gender information from the API
                }
        
        # Format the result to match what the app expects
        formatted_result = {
            "success": True,
            "transcription": results.get("transcript", ""),
            "language": results.get("language_code", "english"),  # Use language_code if available
            "segments": results.get("segments", []),
            "speakers": speakers
        }
        
        return formatted_result
    
    @staticmethod
    async def process_audio_file(
        audio_path: str,
        api_key: Optional[str] = None,
        vad_enabled: bool = True,
        vad_threshold: float = 0.5,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Static convenience method to process an audio file with minimal configuration.
        
        Args:
            audio_path: Path to the audio file
            api_key: Sarvam API key (if None, will use from environment)
            vad_enabled: Whether to use VAD segmentation
            vad_threshold: Threshold for VAD speech detection
            output_dir: Directory to save results and temporary files
            
        Returns:
            Dictionary containing processing results
        """
        processor = SpeechProcessor(api_key)
        processor.configure(
            vad_config={"enabled": vad_enabled, "threshold": vad_threshold}
        )
        
        return await processor.process_audio(audio_path, output_dir)


# Backward compatibility function
async def process_audio_with_diarization(audio_path: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Process audio with diarization (backward compatibility function).
    
    Args:
        audio_path: Path to the audio file
        api_key: Sarvam API key
        
    Returns:
        Dictionary containing processing results
    """
    processor = SpeechProcessor(api_key)
    return await processor.process_audio(audio_path, save_results=False)
