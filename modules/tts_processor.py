"""
TTS Processor module that handles speech synthesis for diarized and translated audio.
Handles routing between Cartesia and Sarvam TTS services based on target language.
"""

import os
import json
import logging
import tempfile
import subprocess
import math
import uuid
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Union, Any
from pydub import AudioSegment

from modules.cartesia_tts import synthesize_speech as cartesia_synthesize
from modules.sarvam_tts import synthesize_speech as sarvam_synthesize
from modules.time_aligned_tts import adjust_segment_duration, process_segments_with_time_alignment, stitch_time_aligned_segments
from utils.file_utils import get_ffmpeg_path

logger = logging.getLogger(__name__)

class TTSProcessor:
    """
    Text-to-Speech processor for synthesizing speech from diarized and translated data.
    Main class for processing TTS synthesis from diarized and translated data.
    """
    
    def __init__(self, output_dir: str, provider: str = 'cartesia', language: str = 'hindi', options: Dict = None, speaker: str = None, speaker_voice_map: Dict = None, session_id: str = None, model: str = None):
        """
        Initialize the TTS processor.
        
        Args:
            output_dir: Output directory for TTS files
            provider: TTS provider to use (cartesia or sarvam)
            language: Target language for TTS
            options: Additional options for TTS
            speaker: Default speaker ID
            speaker_voice_map: Mapping of speaker IDs to voice IDs
            session_id: Unique identifier for this processing session
            model: TTS model to use (for Sarvam)
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.output_dir = output_dir
        self.provider = provider
        self.language = language
        self.speaker = speaker
        self.model = model
        self.options = options or {}
        self.speaker_voice_map = speaker_voice_map or {}
        self.original_duration = 0  # Initialize original_duration
        
        # Initialize segment data
        self.segments = []
        self.segment_files = []
        self.silence_files = []
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create TTS directory
        self.tts_dir = os.path.join(output_dir, "synthesis")
        os.makedirs(self.tts_dir, exist_ok=True)
        
        logger.info(f"Initialized TTS processor with provider {provider} and language {language}")
        if speaker_voice_map:
            logger.info(f"Speaker-voice mapping: {speaker_voice_map}")
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_pre_silence_speech_bundles(self):
        """
        Process bundles of silence and speech segments for time-aligned TTS.
        
        Returns:
            List of bundles with timing information
        """
        bundles = []
        
        # Check if we have any segments
        if not self.segments:
            logger.error("No segments found")
            return []
        
        # Ensure segments are sorted by start time
        self.segments.sort(key=lambda x: x['start_time'])
        
        # Calculate the total audio duration if not already set
        if self.original_duration <= 0 and self.segments:
            # If original_duration is not set, use the end time of the last segment
            self.original_duration = self.segments[-1]['end_time']
            logger.warning(f"Original duration not found in diarization data. Using last segment end time: {self.original_duration}s")
        
        # Process each segment
        for i, current_segment in enumerate(self.segments):
            # Handle the first segment
            if i == 0:
                # Ensure the first silence starts at 0
                initial_silence_start = 0
                initial_silence_end = current_segment['start_time']
                initial_silence_duration = initial_silence_end - initial_silence_start
                
                # Add initial silence if it exists
                if initial_silence_duration > 0:
                    bundles.append({
                        'original': {
                            'start': initial_silence_start,
                            'end': initial_silence_end,
                            'duration': initial_silence_duration
                        },
                        'translated': {
                            'silence_start': initial_silence_start,
                            'silence_end': initial_silence_end,
                            'silence_duration': initial_silence_duration,
                            'speech_start': initial_silence_end,
                            'speech_end': initial_silence_end + round(current_segment['duration']),
                            'speech_duration': round(current_segment['duration'])
                        },
                        'segment': current_segment
                    })
                    
                    # Log the initial silence
                    logger.info(f"Added initial silence bundle: {initial_silence_start} to {initial_silence_end} (duration: {initial_silence_duration})")
            
            # Create bundle for silence between segments
            if i < len(self.segments) - 1:
                next_segment = self.segments[i + 1]
                
                silence_start = current_segment['end_time']
                silence_end = next_segment['start_time']
                silence_duration = silence_end - silence_start
                
                if silence_duration > 0:
                    bundles.append({
                        'original': {
                            'start': silence_start,
                            'end': silence_end,
                            'duration': silence_duration
                        },
                        'translated': {
                            'silence_start': silence_start,
                            'silence_end': silence_end,
                            'silence_duration': silence_duration,
                            'speech_start': silence_end,
                            'speech_end': silence_end + round(next_segment['duration']),
                            'speech_duration': round(next_segment['duration'])
                        },
                        'segment': next_segment
                    })
        
        # Add final silence if needed
        if self.segments and self.original_duration > self.segments[-1]['end_time']:
            final_silence_start = self.segments[-1]['end_time']
            final_silence_end = self.original_duration
            final_silence_duration = final_silence_end - final_silence_start
            
            if final_silence_duration > 0:
                bundles.append({
                    'original': {
                        'start': final_silence_start,
                        'end': final_silence_end,
                        'duration': final_silence_duration
                    },
                    'is_final_silence': True
                })
                
                # Log the final silence
                logger.info(f"Added final silence bundle: {final_silence_start} to {final_silence_end} (duration: {final_silence_duration})")
        
        # Log the total number of bundles
        logger.info(f"Created {len(bundles)} bundles for time-aligned TTS")
        
        return bundles
    
    def synthesize_with_pre_silence_bundling(self, bundles):
        """
        Synthesize speech and stitch with silence based on pre-silence bundling.
        
        Args:
            bundles: List of bundles with timing information
            
        Returns:
            Path to the combined audio file
        """
        combined = AudioSegment.silent(duration=0)
        segment_files = []
        
        # Log the total expected duration based on bundles
        if bundles:
            last_bundle = bundles[-1]
            if 'is_final_silence' in last_bundle and last_bundle['is_final_silence']:
                total_duration = last_bundle['original']['end']
            else:
                total_duration = last_bundle['translated']['speech_end']
            logger.info(f"Expected total duration based on bundles: {total_duration} seconds")
        
        for i, bundle in enumerate(bundles):
            logger.info(f"Processing bundle {i}")
            
            if bundle.get('is_final_silence', False):
                # Add final silence as is
                silence_duration = bundle['original']['duration']
                logger.info(f"Adding final silence of {silence_duration} seconds")
                silence = AudioSegment.silent(duration=silence_duration * 1000)
                combined += silence
                continue
            
            # Add silence portion of bundle
            silence_duration = bundle['translated']['silence_duration']
            if silence_duration > 0:
                logger.info(f"Adding silence of {silence_duration} seconds (from {bundle['translated']['silence_start']} to {bundle['translated']['silence_end']})")
                silence = AudioSegment.silent(duration=silence_duration * 1000)
                combined += silence
            
            # Ensure speech duration is rounded to an integer
            speech_duration = round(bundle['translated']['speech_duration'])
            if speech_duration <= 0:
                logger.info(f"Skipping speech synthesis for bundle {i} as duration is {speech_duration}")
                continue
                
            # Update the bundle with the rounded speech duration
            bundle['translated']['speech_duration'] = speech_duration
            bundle['translated']['speech_end'] = bundle['translated']['speech_start'] + speech_duration
            
            segment = bundle['segment']
            
            # Create temporary file for this segment
            temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
            segment_files.append(temp_file.name)
            
            # Synthesize this segment
            logger.info(f"Synthesizing segment {segment.get('segment_id', 'unknown')} with duration {speech_duration} seconds (from {bundle['translated']['speech_start']} to {bundle['translated']['speech_end']})")
            success = self.synthesize_segment_with_duration(segment, temp_file.name, speech_duration)
            
            # Load synthesized speech
            if success and os.path.exists(temp_file.name) and os.path.getsize(temp_file.name) > 0:
                try:
                    # Use direct FFmpeg command to convert to WAV if needed
                    temp_wav = os.path.join(self.tts_dir, f"temp_segment_{len(segment_files)}.wav")
                    ffmpeg_path = get_ffmpeg_path()
                    subprocess.run([
                        ffmpeg_path,
                        "-y",  # Overwrite output files
                        "-i", temp_file.name,
                        "-acodec", "pcm_s16le",  # Convert to standard WAV format
                        "-ar", "44100",  # 44.1kHz sample rate
                        "-ac", "1",  # Mono
                        temp_wav
                    ], check=True, capture_output=True)
                    
                    # Load the converted WAV file
                    speech_segment = AudioSegment.from_wav(temp_wav)
                    
                    # Verify the duration is as expected
                    actual_duration = len(speech_segment) / 1000
                    logger.info(f"Synthesized segment duration: {actual_duration} seconds (expected {speech_duration} seconds)")
                    
                except Exception as e:
                    logger.error(f"Error loading segment: {str(e)}")
                    speech_segment = AudioSegment.silent(duration=speech_duration * 1000)
            else:
                # Fallback to silence if synthesis failed
                logger.warning(f"Synthesis failed for segment {segment.get('segment_id', 'unknown')}, using silence")
                speech_segment = AudioSegment.silent(duration=speech_duration * 1000)
            
            # Add speech segment
            combined += speech_segment
        
        # Log the actual duration of the combined audio
        actual_duration = len(combined) / 1000
        logger.info(f"Actual combined audio duration: {actual_duration} seconds")
        
        # Save the combined audio
        output_file = os.path.join(self.tts_dir, "combined.mp3")
        combined.export(output_file, format="mp3")
        logger.info(f"Combined audio saved to: {output_file}")
        
        # Clean up temporary files
        for file in segment_files:
            try:
                os.unlink(file)
            except:
                pass
        
        return output_file
    
    def synthesize_segment_with_duration(self, segment, output_path, duration):
        """
        Synthesize a single segment with specified duration.
        
        Args:
            segment: Segment data
            output_path: Path to save the synthesized audio
            duration: Duration in seconds (integer)
            
        Returns:
            bool: Success status
        """
        # Ensure duration is an integer and at least 1 second
        duration = max(1, int(round(duration)))
        
        # Get text to synthesize
        text_to_synthesize = segment.get('translated_text', segment.get('text', ''))
        
        # Skip empty text
        if not text_to_synthesize or text_to_synthesize.strip() == '':
            logger.warning(f"Empty text for segment {segment.get('segment_id', 'unknown')}")
            return False
        
        # Determine language to use
        lang = segment.get('language', self.language)
        
        # Normalize language code
        normalized_lang = lang.lower()
        if normalized_lang in ['hi', 'hin', 'hindi']:
            normalized_lang = 'hindi'
        
        # Get speaker_id and voice_id for this segment
        speaker_id = segment.get('speaker', self.speaker)
        voice_id = None
        
        # Log speaker ID for debugging
        logger.info(f"Segment {segment.get('segment_id', 'unknown')} has speaker ID: {speaker_id}")
        
        # Use appropriate TTS provider
        if self.provider == 'cartesia' and normalized_lang in ['hindi', 'hi']:
            # If speaker_id exists, try to get the corresponding voice_id from the mapping
            if speaker_id and speaker_id in self.speaker_voice_map:
                voice_id = self.speaker_voice_map.get(speaker_id)
                logger.info(f"Found mapped voice {voice_id} for speaker {speaker_id}")
            else:
                logger.info(f"No voice mapping found for speaker {speaker_id}. Available mappings: {self.speaker_voice_map}")
            
            # If no voice_id found, use default
            if not voice_id:
                voice_id = "6452a836-cd72-45bc-ab0d-b47b999594dd"  # Default to Dhwani's voice
                logger.info(f"Using default voice {voice_id} for speaker {speaker_id}")
            
            logger.info(f"Using Cartesia TTS for segment {segment.get('segment_id', 'unknown')} with language {normalized_lang} and voice {voice_id}")
            
            # Call Cartesia without duration parameter
            success = cartesia_synthesize(
                text=text_to_synthesize,
                output_path=output_path,
                voice_id=voice_id
            )
            
            return success
        else:
            # Use Sarvam TTS for other languages
            logger.info(f"Using Sarvam TTS for segment {segment.get('segment_id', 'unknown')} with language {normalized_lang}")
            
            # Get voice_id for Sarvam if available
            if speaker_id and speaker_id in self.speaker_voice_map:
                voice_id = self.speaker_voice_map.get(speaker_id)
                logger.info(f"Found mapped voice {voice_id} for speaker {speaker_id}")
            
            try:
                sarvam_synthesize(
                    text=text_to_synthesize,
                    output_path=output_path,
                    language=normalized_lang,
                    speaker=voice_id
                )
                return True
            except Exception as e:
                logger.error(f"Sarvam TTS failed: {str(e)}")
                return False
    
    def process_tts(self, diarization_file=None):
        """
        Process TTS for all segments using time-aligned approach.
        
        Args:
            diarization_file: Path to diarization file (optional)
            
        Returns:
            str: Path to the combined audio file
        """
        # Load diarization data
        if not diarization_file:
            diarization_file = os.path.join(self.output_dir, "diarization.json")
        
        # Check if diarization file exists
        if not os.path.exists(diarization_file):
            # Check if we have a translated diarization file
            translated_file = os.path.join(self.output_dir, "diarization_translated.json")
            if os.path.exists(translated_file):
                diarization_file = translated_file
                logger.info(f"Found diarized translation file: {diarization_file}")
            else:
                logger.error(f"Diarization file not found: {diarization_file}")
                return None
        
        # Load diarization data
        with open(diarization_file, 'r') as f:
            diarization_data = json.load(f)
        
        # Extract segments
        if isinstance(diarization_data, dict) and 'segments' in diarization_data:
            self.segments = diarization_data['segments']
            self.original_duration = diarization_data.get('audio_duration', 0)  # Set original_duration
        elif isinstance(diarization_data, list):
            self.segments = diarization_data
        else:
            logger.error(f"Invalid diarization data format")
            return None
        
        # Check if we have any segments
        if not self.segments:
            logger.error(f"No segments found in diarization data")
            return None
        
        # Check if we have language information in the segments
        target_language = None
        for segment in self.segments:
            if 'language' in segment and segment['language']:
                target_language = segment['language']
                break
        
        # If target language found, update the processor's language
        if target_language:
            logger.info(f"Using target language for TTS: {target_language}")
            self.language = target_language
        else:
            logger.warning("No target language found in segments. Using default language.")
        
        try:
            # Process segments using pre-silence speech bundling
            logger.info("Processing segments using pre-silence speech bundling approach")
            bundles = self.process_pre_silence_speech_bundles()
            
            if not bundles:
                logger.error("Failed to process pre-silence speech bundles")
                return None
            
            # Synthesize and stitch audio using pre-silence bundling
            logger.info("Synthesizing audio with pre-silence bundling")
            combined_audio_path = self.synthesize_with_pre_silence_bundling(bundles)
            
            if not combined_audio_path or not os.path.exists(combined_audio_path):
                logger.error("Failed to synthesize with pre-silence bundling")
                return None
            
            # Create the final output file with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_output = os.path.join(self.tts_dir, f"final_output_{timestamp}.wav")
            
            # Copy the combined audio to the final output file
            try:
                # Load the combined audio
                combined_audio = AudioSegment.from_file(combined_audio_path)
                
                # Export to final output file
                combined_audio.export(final_output, format="wav")
                logger.info(f"Final audio saved to: {final_output}")
            except Exception as e:
                logger.error(f"Error creating final output file: {str(e)}")
                return None
            
            # Save synthesis details
            synthesis_details = {
                "segments": self.segments,
                "silence_padding": self.extract_silence_padding_from_bundles(bundles),
                "provider": self.provider,
                "language": self.language,
                "file": os.path.basename(final_output)
            }
            
            # Drop 'text' and 'translated_text' fields from each segment before saving
            if isinstance(synthesis_details, dict) and "segments" in synthesis_details:
                for segment in synthesis_details["segments"]:
                    segment.pop("text", None)
                    segment.pop("translated_text", None)
            
            # Save synthesis details to file
            details_file = os.path.join(self.tts_dir, f"synthesis_details_{self.speaker}.json")
            with open(details_file, 'w') as f:
                json.dump(synthesis_details, f, indent=2)
            logger.info(f"Synthesis details saved to: {details_file}")
            
            return final_output
            
        except Exception as e:
            logger.error(f"Error in process_tts: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def extract_silence_padding_from_bundles(self, bundles):
        """
        Extract silence padding information from bundles.
        
        Args:
            bundles: List of bundles with timing information
            
        Returns:
            List of silence padding information
        """
        silence_padding = []
        for bundle in bundles:
            if bundle.get('is_final_silence', False):
                silence_padding.append({
                    "padding_id": "final_silence",
                    "start_time": bundle['original']['start'],
                    "end_time": bundle['original']['end'],
                    "duration": bundle['original']['duration']
                })
            else:
                silence_padding.append({
                    "padding_id": f"silence_{len(silence_padding)}",
                    "start_time": bundle['translated']['silence_start'],
                    "end_time": bundle['translated']['silence_end'],
                    "duration": bundle['translated']['silence_duration']
                })
        
        return silence_padding
    
    def synthesize_segment(self, segment: Dict) -> str:
        """
        Synthesize speech for a single segment.
        
        Args:
            segment: Dictionary containing segment details
        
        Returns:
            Path to the synthesized audio file
        """
        try:
            # Get text to synthesize
            text_to_synthesize = segment.get('translated_text', segment.get('text', ''))
            if not text_to_synthesize or text_to_synthesize.strip() == '':
                logger.warning(f"Empty text for segment {segment.get('segment_id', 'unknown')}, creating silence file")
                
                # Calculate duration from segment timing
                start_time = float(segment.get('start_time', 0))
                end_time = float(segment.get('end_time', start_time + 1.0))
                duration = end_time - start_time
                
                # Create silence file with appropriate duration
                duration_ms = int(duration * 1000)  # Convert to milliseconds
                
                # Create temporary file for output
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    pass
                
                # Add segment to segment files list
                self.segment_files.append(temp_file.name)
                
                # Create silence with the calculated duration
                logger.info(f"Creating silence file for segment {segment.get('segment_id', 'unknown')} with duration {duration:.2f}s")
                return create_silent_wav(duration_ms, temp_file.name)
            
            # Get target language - check multiple possible keys with fallback to logger data
            target_lang = segment.get('language', None)
            if not target_lang or target_lang == 'unknown':
                target_lang = segment.get('target_language', None)
            
            # If still not found, use the logger's language setting
            if not target_lang or target_lang == 'unknown':
                target_lang = self.language
                
            logger.info(f"Using target language for TTS: {target_lang}")
            
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                pass
            
            # Language mapping for normalization
            language_map = {
                'en': 'english',
                'hi': 'hindi',
                'te': 'telugu',
                'ta': 'tamil',
                'kn': 'kannada',
                'ml': 'malayalam',
                'bn': 'bengali'
            }
            
            # Normalize language name
            normalized_lang = language_map.get(target_lang.lower(), target_lang.lower())
            
            # Add segment to segment files list
            self.segment_files.append(temp_file.name)
            
            if normalized_lang == 'hindi':
                # Get speaker_id and voice_id for this segment
                speaker_id = segment.get('speaker', self.speaker)
                voice_id = None
                
                # Log speaker ID for debugging
                logger.info(f"Segment {segment.get('segment_id', 'unknown')} has speaker ID: {speaker_id}")
                
                # If speaker_id exists, try to get the corresponding voice_id from the mapping
                if speaker_id and speaker_id in self.speaker_voice_map:
                    voice_id = self.speaker_voice_map.get(speaker_id)
                    logger.info(f"Found mapped voice {voice_id} for speaker {speaker_id}")
                else:
                    logger.info(f"No voice mapping found for speaker {speaker_id}. Available mappings: {self.speaker_voice_map}")
                
                # If no voice_id found, use default
                if not voice_id:
                    voice_id = "6452a836-cd72-45bc-ab0d-b47b999594dd"  # Default to Dhwani's voice
                    logger.info(f"Using default voice {voice_id} for speaker {speaker_id}")
                
                logger.info(f"Using Cartesia TTS for segment {segment.get('segment_id', 'unknown')} with language {normalized_lang} and voice {voice_id}")
                
                # Call Cartesia without duration parameter
                success = cartesia_synthesize(
                    text=text_to_synthesize,
                    output_path=temp_file.name,
                    voice_id=voice_id
                )
                
                return success
            else:
                # Get speaker_id and voice_id for this segment
                speaker_id = segment.get('speaker', self.speaker)
                voice_id = None
                
                # Log speaker ID for debugging
                logger.info(f"Segment {segment.get('segment_id', 'unknown')} has speaker ID: {speaker_id}")
                
                # If speaker_id exists, try to get the corresponding voice_id from the mapping
                if speaker_id and speaker_id in self.speaker_voice_map:
                    voice_id = self.speaker_voice_map.get(speaker_id)
                    logger.info(f"Found mapped voice {voice_id} for speaker {speaker_id}")
                else:
                    logger.info(f"No voice mapping found for speaker {speaker_id}. Available mappings: {self.speaker_voice_map}")
                
                # If no voice_id found, use default speaker
                speaker = voice_id if voice_id else 'anushka'
                logger.info(f"Using speaker {speaker} for Sarvam TTS")
                
                logger.info(f"Using Sarvam TTS for segment {segment.get('segment_id', 'unknown')} with language {normalized_lang} and speaker {speaker}")
                
                # Use Sarvam TTS for other languages
                sarvam_synthesize(
                    text=text_to_synthesize,
                    output_path=temp_file.name,
                    language=normalized_lang,
                    speaker=speaker,
                    model=segment.get('model', self.model or 'bulbul:v2'),
                    pitch=0,  # Default value
                    pace=segment.get('pace', 1.0),  # Use segment's pace or default to 1.0
                    loudness=1.0  # Default value
                )
                logger.info(f"Sarvam TTS synthesis completed for segment {segment.get('segment_id', 'unknown')}")
            
            # Check if the file was created
            if not os.path.exists(temp_file.name) or os.path.getsize(temp_file.name) == 0:
                logger.warning(f"TTS failed to create audio for segment {segment.get('segment_id', 'unknown')}")
                # Create a silent audio file as fallback
                return create_silent_wav(1000)
                
            return temp_file.name
            
        except Exception as e:
            logger.error(f"Error synthesizing segment {segment.get('segment_id', 'unknown')}: {str(e)}")
            # Create a silent audio file as fallback
            return create_silent_wav(1000)
    
    def stitch_audio(self) -> tuple[str, float, list]:
        """
        Combine all audio segments with appropriate silence padding.
        
        Returns:
            Tuple of (output_file, average_pace, silence_padding)
        """
        try:
            # Create output directory
            tts_dir = os.path.join(self.output_dir, "tts")
            os.makedirs(tts_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(tts_dir, f"final_output_{timestamp}.wav")
            
            # Create temporary file for combined audio
            temp_file = os.path.join(tts_dir, "temp.wav")
            
            # Combine audio segments with silence
            combined = AudioSegment.silent(duration=0)
            total_duration = 0
            silence_padding = []
            padding_id = 1
            
            # Process each segment
            for i in range(len(self.segments)):
                segment_file = self.segment_files[i]
                
                # Check if file exists and has content
                if not os.path.exists(segment_file) or os.path.getsize(segment_file) == 0:
                    logger.warning(f"Segment file {segment_file} does not exist or is empty")
                    segment = AudioSegment.silent(duration=1000)  # 1 second of silence as fallback
                else:
                    try:
                        # Use direct FFmpeg command to convert to WAV if needed
                        temp_wav = os.path.join(tts_dir, f"temp_segment_{i}.wav")
                        ffmpeg_path = get_ffmpeg_path()
                        subprocess.run([
                            ffmpeg_path,
                            "-y",  # Overwrite output files
                            "-i", segment_file,
                            "-acodec", "pcm_s16le",  # Convert to standard WAV format
                            "-ar", "44100",  # 44.1kHz sample rate
                            "-ac", "1",  # Mono
                            temp_wav
                        ], check=True, capture_output=True)
                        
                        # Load the converted WAV file
                        segment = AudioSegment.from_wav(temp_wav)
                    except Exception as e:
                        logger.error(f"Error loading segment {i}: {str(e)}")
                        segment = AudioSegment.silent(duration=1000)  # 1 second of silence as fallback
                
                # Add segment
                combined += segment
                total_duration += len(segment) / 1000  # Convert ms to seconds
                
                # Add silence between segments
                if i < len(self.segments) - 1:
                    silence_duration = self.segments[i+1].get('start_time', self.segments[i+1].get('start', 0)) - self.segments[i].get('end_time', self.segments[i].get('end', 0))
                    silence = AudioSegment.silent(duration=silence_duration * 1000)  # Convert seconds to ms
                    combined += silence
                    
                    silence_padding.append({
                        "padding_id": f"padding_{padding_id}",
                        "start_time": self.segments[i].get('end_time', self.segments[i].get('end', 0)),
                        "end_time": self.segments[i+1].get('start_time', self.segments[i+1].get('start', 0)),
                        "duration": silence_duration
                    })
                    padding_id += 1
                    total_duration += silence_duration
            
            # Add final silence if needed
            # Check if we have original audio duration information
            original_audio_duration = None
            try:
                # Try to get original audio duration from diarization file
                diarization_file = os.path.join(self.output_dir, "diarization.json")
                if os.path.exists(diarization_file):
                    with open(diarization_file, 'r') as f:
                        diarization_data = json.load(f)
                        if isinstance(diarization_data, dict) and 'audio_duration' in diarization_data:
                            original_audio_duration = diarization_data['audio_duration']
                        elif isinstance(diarization_data, dict) and 'metadata' in diarization_data and 'duration' in diarization_data['metadata']:
                            original_audio_duration = diarization_data['metadata']['duration']
            except Exception as e:
                logger.warning(f"Error getting original audio duration: {str(e)}")
            
            # If we have the last segment and original audio duration
            if len(self.segments) > 0 and original_audio_duration:
                last_segment = self.segments[-1]
                last_segment_end = last_segment.get('end_time', last_segment.get('end', 0))
                
                # If original audio is longer than our last segment
                if original_audio_duration > last_segment_end:
                    final_silence_duration = original_audio_duration - last_segment_end
                    logger.info(f"Adding final silence of {final_silence_duration} seconds")
                    
                    # Add silence at the end
                    final_silence = AudioSegment.silent(duration=final_silence_duration * 1000)
                    combined += final_silence
                    
                    # Add to silence padding list
                    silence_padding.append({
                        "padding_id": f"padding_{padding_id}",
                        "start_time": last_segment_end,
                        "end_time": original_audio_duration,
                        "duration": final_silence_duration
                    })
                    total_duration += final_silence_duration
            
            # Calculate average pace
            input_duration = sum(segment.get('end_time', segment.get('end', 0)) - segment.get('start_time', segment.get('start', 0)) for segment in self.segments)
            average_pace = input_duration / total_duration if total_duration > 0 else 0.0
            
            # Export combined audio to temp file first
            combined.export(temp_file, format="wav")
            logger.info(f"Temporary combined audio saved to: {temp_file}")
            
            # Then export to final output file
            combined.export(output_file, format="wav")
            logger.info(f"Final audio saved to: {output_file}")
            
            return output_file, average_pace, silence_padding
            
        except Exception as e:
            logger.error(f"Error in stitch_audio: {str(e)}")
            raise

    def cleanup(self) -> None:
        """
        Clean up temporary files.
        """
        try:
            # Remove temporary files
            for file in self.segment_files + self.silence_files:
                try:
                    os.remove(file)
                except Exception as e:
                    logger.warning(f"Error removing file {file}: {str(e)}")
            
            self.segment_files.clear()
            self.silence_files.clear()
            logger.info("Temporary files cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            raise

    def process_tts(self, diarization_file: str = None) -> str:
        """
        Process TTS synthesis for the given diarization file.
        
        Args:
            diarization_file: Path to the diarization JSON file (optional)
            
        Returns:
            str: Path to the final synthesized audio file
        """
        try:
            # Ensure output directories exist
            tts_dir = os.path.join(self.output_dir, "tts")
            os.makedirs(tts_dir, exist_ok=True)
            
            synthesis_dir = os.path.join(self.output_dir, "synthesis")
            os.makedirs(synthesis_dir, exist_ok=True)
            
            # Check for diarized_translation.json in multiple locations
            possible_paths = [
                os.path.join(self.output_dir, "transcription", "diarization_translated.json"),
                os.path.join(self.output_dir, "diarization_translated.json"),
                os.path.join(self.output_dir, "diarized_translated.json")
            ]
            
            translation_file = None
            for path in possible_paths:
                if os.path.exists(path):
                    translation_file = path
                    logger.info(f"Found diarized translation file: {translation_file}")
                    break
            
            if translation_file:
                with open(translation_file, 'r') as f:
                    data = json.load(f)
                    
                # Process the translated diarization data
                if isinstance(data, dict):
                    # Extract target language if available
                    target_language = data.get('target_language', None)
                    
                    # If target_language is not explicitly set, try to infer it
                    if not target_language:
                        # Check if any segment has language information
                        if 'segments' in data and data['segments']:
                            for segment in data['segments']:
                                if 'language' in segment and segment['language']:
                                    target_language = segment['language']
                                    logger.info(f"Inferred target language from segment: {target_language}")
                                    break
                    
                    if target_language:
                        logger.info(f"Using target language for TTS: {target_language}")
                        # Update language for TTS
                        self.language = target_language
                    else:
                        logger.warning("No target language found in translation data. TTS may use incorrect language.")
                    
                    # Get segments
                    if 'segments' in data:
                        self.segments = data['segments']
                        # Update the language in all segments if target_language is available
                        if target_language:
                            for segment in self.segments:
                                segment['language'] = target_language
                                # Ensure segment has segment_id for better logging
                                if 'segment_id' not in segment:
                                    segment['segment_id'] = f"seg_{self.segments.index(segment):03d}"
                elif isinstance(data, list):
                    self.segments = data
                    # Try to find language in the first segment with a language field
                    target_language = None
                    for segment in self.segments:
                        if 'language' in segment and segment['language']:
                            target_language = segment['language']
                            logger.info(f"Found language in segment: {target_language}")
                            break
                    
                    if target_language:
                        # Update all segments with the language
                        for i, segment in enumerate(self.segments):
                            segment['language'] = target_language
                            # Ensure segment has segment_id for better logging
                            if 'segment_id' not in segment:
                                segment['segment_id'] = f"seg_{i:03d}"
                    else:
                        logger.warning("No language found in segments. TTS may use incorrect language.")
                else:
                    logger.error(f"Unexpected format in diarized translation file")
                    raise ValueError("Invalid diarized translation format")
            else:
                # Fall back to the provided diarization file
                logger.info(f"Diarized translation not found, using: {diarization_file}")
                self.process_diarization(diarization_file)
            
            # Process each segment
            for i, segment in enumerate(self.segments):
                logger.info(f"Processing segment {i} with text: {segment.get('text', '')} and language: {segment.get('language', 'unknown')}")
                self.synthesize_segment(segment)
            
            # Combine everything
            final_audio, average_pace, silence_padding = self.stitch_audio()
            logger.info(f"Stitch_audio returned silence padding: {silence_padding}")
            
            # Get padding duration from logger's processing summary
            total_padding_duration = sum(pad["duration"] for pad in silence_padding)
            
            # Update final output details
            logger.info(f"Final audio duration: {sum(segment.get('end_time', segment.get('end', 0)) - segment.get('start_time', segment.get('start', 0)) for segment in self.segments) + total_padding_duration}")
            logger.info(f"Final audio size: {os.path.getsize(final_audio)}")
            logger.info(f"Padding duration: {total_padding_duration}")
            
            # Save synthesis details
            try:
                synthesis_details = {
                    "segments": self.segments,
                    "silence_padding": silence_padding,
                    "provider": self.provider,
                    "language": self.language
                }
                
                # Drop 'text' and 'translated_text' fields from each segment before saving
                if isinstance(synthesis_details, dict) and "segments" in synthesis_details:
                    for segment in synthesis_details["segments"]:
                        segment.pop("text", None)
                        segment.pop("translated_text", None)
                
                details_file = os.path.join(self.tts_dir, f"synthesis_details_{self.speaker}.json")
                with open(details_file, 'w') as f:
                    json.dump(synthesis_details, f, indent=2)
                logger.info(f"Synthesis details saved successfully")
            except Exception as save_error:
                logger.error(f"Error saving synthesis details: {str(save_error)}")
                import traceback
                logger.error(traceback.format_exc())
            
            # Clean up temporary files
            self.cleanup()
            
            return final_audio
            
        except Exception as e:
            logger.error(f"Error in process_tts: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise

    def process_diarization(self, diarization_file: str) -> None:
        """
        Process diarization file and extract segments.
        
        Args:
            diarization_file: Path to the diarization JSON file
        """
        try:
            with open(diarization_file, 'r') as f:
                data = json.load(f)
                
            # Handle both dictionary and list formats
            if isinstance(data, dict):
                # If data is a dictionary, extract segments
                self.segments = data.get('segments', [])
                self.original_duration = data.get('audio_duration', 0)
                # Log basic statistics if available
                logger.info(f"Processing {len(self.segments)} segments")
                if 'target_language' in data:
                    logger.info(f"Target language: {data.get('target_language', 'unknown')}")
            elif isinstance(data, list):
                # If data is already a list of segments
                self.segments = data
                logger.info(f"Processing {len(self.segments)} segments from list format")
            else:
                logger.error(f"Unexpected data format: {type(data)}")
                raise ValueError(f"Unexpected data format: {type(data)}")
                
            if not self.segments:
                logger.error("No segments found in diarization data")
                raise ValueError("No segments found in diarization data")
                
            # Add segments to logger
            for segment in self.segments:
                segment_data = {
                    "segment_id": segment.get('segment_id', 'unknown'),
                    "speaker": segment.get('speaker', 'unknown'),
                    "start_time": segment.get('start_time', 0),
                    "end_time": segment.get('end_time', 0),
                    "duration": segment.get('end_time', 0) - segment.get('start_time', 0),
                    "text": segment.get('text', ''),
                    "gender": segment.get('gender', 'unknown'),
                    "pace": segment.get('pace', 0.5)
                }
                logger.info(f"Adding segment {segment.get('segment_id', 'unknown')} to logger")
                
        except Exception as e:
            logger.error(f"Error processing diarization file: {str(e)}")
            raise

    def process_tts_with_time_alignment(self, diarization_file=None):
        """
        Process TTS with time alignment to match original segment durations.
        
        This method synthesizes speech for each segment, then adjusts the duration
        to match the original audio segment, ensuring temporal alignment.
        
        Args:
            diarization_file: Path to diarization file (optional)
            
        Returns:
            str: Path to the final time-aligned audio file
        """
        # Load diarization data
        if not diarization_file:
            diarization_file = os.path.join(self.output_dir, "diarization.json")
        
        # Check if diarization file exists
        if not os.path.exists(diarization_file):
            # Check if we have a translated diarization file
            translated_file = os.path.join(self.output_dir, "diarization_translated.json")
            if os.path.exists(translated_file):
                diarization_file = translated_file
                logger.info(f"Found diarized translation file: {diarization_file}")
            else:
                logger.error(f"Diarization file not found: {diarization_file}")
                return None
        
        # Load diarization data
        with open(diarization_file, 'r') as f:
            diarization_data = json.load(f)
        
        # Extract segments
        if isinstance(diarization_data, dict) and 'segments' in diarization_data:
            self.segments = diarization_data['segments']
            self.original_duration = diarization_data.get('audio_duration', 0)
        elif isinstance(diarization_data, list):
            self.segments = diarization_data
        else:
            logger.error(f"Invalid diarization data format")
            return None
        
        # Check if we have any segments
        if not self.segments:
            logger.error(f"No segments found in diarization data")
            return None
        
        # Create TTS directory if it doesn't exist
        os.makedirs(self.tts_dir, exist_ok=True)
        
        # Step 1: Synthesize each segment without time alignment
        logger.info("Step 1: Synthesizing individual segments")
        
        # Check for merged segments file first (preferred)
        merged_file = os.path.join(self.output_dir, "diarization_translated_merged.json")
        diarization_file = os.path.join(self.output_dir, "diarization_translated.json")
        regular_diarization_file = os.path.join(self.output_dir, "diarization.json")
        
        # Determine which segments file to use
        if os.path.exists(merged_file):
            logger.info(f"Using merged segments file: {merged_file}")
            with open(merged_file, 'r') as f:
                data = json.load(f)
                # Check if this is a merged segments file with the expected structure
                if 'merged_segments' in data:
                    # Extract just the merged_segments array
                    self.segments = data.get('merged_segments', [])
                    original_count = data.get('original_segment_count', 0)
                    logger.info(f"Loaded {len(self.segments)} merged segments (from {original_count} original segments)")
                else:
                    # Fall back to treating the whole file as segments
                    self.segments = data.get('segments', []) if isinstance(data, dict) else data
                    logger.info(f"Loaded {len(self.segments)} segments from merged file (standard format)")
        elif os.path.exists(diarization_file):
            logger.info(f"Merged segments file not found, using translated diarization file: {diarization_file}")
            with open(diarization_file, 'r') as f:
                data = json.load(f)
                self.segments = data.get('segments', [])
                logger.info(f"Loaded {len(self.segments)} segments from translated diarization")
        elif os.path.exists(regular_diarization_file):
            logger.info(f"Using regular diarization file: {regular_diarization_file}")
            with open(regular_diarization_file, 'r') as f:
                data = json.load(f)
                self.segments = data.get('segments', [])
                logger.info(f"Loaded {len(self.segments)} segments from regular diarization")
        else:
            logger.error("No diarization file found")
            return None
        
        # Synthesize each segment
        for i, segment in enumerate(self.segments):
            segment_id = segment.get('segment_id', f"seg_{i:03d}")
            
            # Create output path for this segment
            segment_output = os.path.join(self.tts_dir, f"segment_{segment_id}.wav")
            
            # Synthesize this segment
            logger.info(f"Synthesizing segment {segment_id}")
            success = self.synthesize_segment_with_duration(segment, segment_output, 0)  # 0 means no specific duration
            
            if not success:
                logger.warning(f"Failed to synthesize segment {segment_id}")
        
        # Step 2: Get segments file path for timing
        # If we're using merged segments, we should use the merged file for timing as well
        if os.path.exists(merged_file):
            timing_file = merged_file
            logger.info(f"Using merged segments file for timing: {timing_file}")
        else:
            timing_file = regular_diarization_file
            logger.info(f"Using regular diarization file for timing: {timing_file}")
        
        if not os.path.exists(timing_file):
            logger.error(f"Timing file not found: {timing_file}")
            return None
        
        # Step 3: Process time alignment
        logger.info("Step 3: Processing time alignment")
        dir_session_id = os.path.basename(self.output_dir)
        if dir_session_id.startswith("session_"):
            logger.info(f"Using directory-based session ID for file paths: {dir_session_id}")
            session_id = dir_session_id
        else:
            session_id = self.session_id
        
        alignment_metadata = process_segments_with_time_alignment(
            session_id,
            os.path.dirname(self.output_dir),  # Get parent directory
            timing_file,  # Use the timing file we identified
            self.tts_dir
        )
        
        # Step 4: Stitch time-aligned segments
        logger.info("Step 4: Stitching time-aligned segments")
        # Try to extract session ID from directory path
        dir_session_id = None
        if self.output_dir and "/" in self.output_dir:
            dir_parts = self.output_dir.split("/")
            for part in dir_parts:
                if part.startswith("session_"):
                    dir_session_id = part
                    break
        
        # Try multiple possible locations for the audio file
        original_audio_path = None
        possible_paths = [
            # First try the path where YouTube audio is saved (.mp3)
            os.path.join(os.path.dirname(self.output_dir), self.session_id, "audio", f"{self.session_id}.mp3"),
            
            # Then try the same path but with .wav extension
            os.path.join(os.path.dirname(self.output_dir), self.session_id, "audio", f"{self.session_id}.wav"),
            
            # Then try the old paths as fallbacks
            os.path.join(self.output_dir, "audio", f"{dir_session_id}.wav") if dir_session_id else None,
            os.path.join(self.output_dir, "audio", f"session_{self.session_id}.wav"),
            
            # Try without session_ prefix as well
            os.path.join(self.output_dir, "audio", f"{self.session_id}.wav"),
            os.path.join(self.output_dir, "audio", f"{self.session_id}.mp3"),
        ]
        
        # Filter out None values
        possible_paths = [path for path in possible_paths if path]
        
        # Try each path until we find one that exists
        for path in possible_paths:
            if os.path.exists(path):
                original_audio_path = path
                logger.info(f"Found original audio at: {original_audio_path}")
                break
        
        if not original_audio_path or not os.path.exists(original_audio_path):
            logger.warning(f"Original audio file not found in any of the expected locations, will use segment timing only")
            for path in possible_paths:
                logger.debug(f"Tried path: {path} (exists: {os.path.exists(path) if path else False})")
            original_audio_path = None  # Ensure it's None if not found
        else:
            logger.info(f"Using original audio for timing: {original_audio_path}")

        # Create timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        output_file = stitch_time_aligned_segments(
            session_id,
            os.path.dirname(self.output_dir),  # Get parent directory
            alignment_metadata,
            output_file=os.path.join(self.tts_dir, f"final_output_{timestamp}.wav"),
            original_audio_path=original_audio_path
        )
        
        if not output_file or not os.path.exists(output_file):
            logger.error("Failed to stitch time-aligned segments")
            return None
        
        # Step 5: Save synthesis details
        synthesis_details = {
            "time_aligned": True,
            "segments": self.segments,
            "provider": self.provider,
            "language": self.language,
            "file": os.path.basename(output_file),
            "alignment_metadata": alignment_metadata
        }
        
        # Drop 'text' and 'translated_text' fields from each segment before saving
        if isinstance(synthesis_details, dict) and "segments" in synthesis_details:
            for segment in synthesis_details["segments"]:
                segment.pop("text", None)
                segment.pop("translated_text", None)
        
        # Save synthesis details to file
        details_file = os.path.join(self.tts_dir, f"synthesis_details_{timestamp}.json")
        with open(details_file, 'w') as f:
            json.dump(synthesis_details, f, indent=2)
        
        logger.info(f"Synthesis details saved to: {details_file}")
        
        return output_file
    
def process_tts(session_id: str, output_dir: str, diarization_file: str = None) -> str:
    """
    Process TTS synthesis for the given diarization file.
    
    Args:
        session_id: Unique identifier for this processing session
        output_dir: Directory where output files should be saved
        diarization_file: Path to the diarization JSON file (optional)
        
    Returns:
        Path to the final synthesized audio file
    """
    try:
        # Initialize processor with session details
        processor = TTSProcessor(output_dir, session_id)
        
        # Process diarization file
        processor.process_diarization(diarization_file)
        
        # Process each segment
        for i, segment in enumerate(processor.segments):
            logger.info(f"Processing segment {i} with text: {segment['text']}")
            processor.synthesize_segment(segment)
        
        # Combine everything
        final_audio, average_pace, silence_padding = processor.stitch_audio()
        logger.info(f"Stitch_audio returned silence padding: {silence_padding}")
        
        # Get padding duration from logger's processing summary
        total_padding_duration = sum(pad["duration"] for pad in silence_padding)
        logger.info(f"Total padding duration from logger: {total_padding_duration}")
        
        # Update final output details
        logger.info(f"Final audio duration: {sum(segment['end_time'] - segment['start_time'] for segment in processor.segments) + total_padding_duration}")
        logger.info(f"Final audio size: {os.path.getsize(final_audio)}")
        logger.info(f"Padding duration: {total_padding_duration}")
        
        # Save synthesis details
        synthesis_details = {
            "segments": processor.segments,
            "silence_padding": silence_padding,
            "provider": processor.provider,
            "language": processor.language
        }
        
        # Drop 'text' and 'translated_text' fields from each segment before saving
        if isinstance(synthesis_details, dict) and "segments" in synthesis_details:
            for segment in synthesis_details["segments"]:
                segment.pop("text", None)
                segment.pop("translated_text", None)
        
        details_file = os.path.join(processor.tts_dir, f"synthesis_details_{processor.speaker}.json")
        with open(details_file, 'w') as f:
            json.dump(synthesis_details, f, indent=2)
        logger.info(f"Synthesis details saved to: {details_file}")
        
        # Cleanup temporary files
        processor.cleanup()
        
        return final_audio
        
    except Exception as e:
        logger.error(f"Error in TTS processing: {str(e)}")
        raise

def create_silent_wav(duration_ms, output_path=None):
    """
    Create a silent WAV file with the specified duration.
    
    Args:
        duration_ms: Duration in milliseconds
        output_path: Path to save the WAV file (optional)
        
    Returns:
        Path to the created WAV file
    """
    try:
        # Create silent audio segment
        silent_segment = AudioSegment.silent(duration=duration_ms)
        
        # Create temporary file if output_path not provided
        if not output_path:
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            output_path = temp_file.name
            temp_file.close()
        
        # Export to WAV
        silent_segment.export(output_path, format="wav")
        
        return output_path
    except Exception as e:
        logger.error(f"Error creating silent WAV: {str(e)}")
        return None
