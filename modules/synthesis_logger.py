"""
Module for logging synthesis details and statistics.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class SynthesisLogger:
    """
    Logger for synthesis operations that captures detailed statistics and logs.
    """
    def __init__(self, session_id: str, output_dir: str):
        """
        Initialize the synthesis logger.
        
        Args:
            session_id: Unique identifier for this processing session
            output_dir: Directory where output files should be saved
        """
        self.session_id = session_id
        self.output_dir = output_dir
        self.synthesis_dir = os.path.join(output_dir, "synthesis")
        
        # Ensure synthesis directory exists
        os.makedirs(self.synthesis_dir, exist_ok=True)
        
        # Initialize data structure
        self.data = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "provider": None,
            "language": None,
            "speaker": None,
            "model": None,
            "segments": [],
            "silence_padding": [],
            "final_output": {
                "file": None,
                "format": None,
                "total_duration": 0.0,
                "segments_count": 0,
                "size_bytes": 0,
                "padding_duration": 0.0
            },
            "processing_summary": {
                "total_segments": 0,
                "total_duration": 0.0,
                "input_duration": 0.0,
                "padding_duration": 0.0,
                "average_pace": 0.0,
                "average_segment_duration": 0.0
            }
        }
        
        # Initialize log file path
        self.log_file = os.path.join(self.synthesis_dir, f"synthesis_details_{self.session_id}.json")

    def set_provider_details(self, provider: str, language: str, speaker: Optional[str] = None, model: Optional[str] = None) -> None:
        """
        Set provider and language details.
        
        Args:
            provider: Name of the TTS provider (e.g., 'sarvam', 'cartesia')
            language: Target language for synthesis
            speaker: Optional speaker ID
            model: Optional model name
        """
        self.data["provider"] = provider
        self.data["language"] = language
        self.data["speaker"] = speaker
        self.data["model"] = model
        logging.info(f"Set provider details for session {self.session_id}")

    def add_segment(self, segment_data: Dict) -> None:
        """
        Add a segment to the log.
        
        Args:
            segment_data: Dictionary containing segment details
        """
        self.data["segments"].append(segment_data)
        logging.info(f"Added segment to logger")

    def add_silence_padding(self, start_time: float, end_time: float, duration: float, padding_id: str) -> None:
        """
        Add silence padding details to the log.
        
        Args:
            start_time: Start time of the silence period
            end_time: End time of the silence period
            duration: Duration of the silence in seconds
            padding_id: Unique identifier for this padding segment
        """
        # Check if this padding ID already exists
        if any(pad["padding_id"] == padding_id for pad in self.data["silence_padding"]):
            logging.warning(f"Silence padding with ID {padding_id} already exists, skipping")
            return
            
        # Create silence padding entry
        padding_entry = {
            "padding_id": padding_id,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration
        }
        
        # Add to silence padding array
        self.data["silence_padding"].append(padding_entry)
        self.data["processing_summary"]["padding_duration"] += duration
        logging.info(f"Added silence padding: {padding_entry}")

    def update_final_output(self, output_file: str, format: str, duration: float, size_bytes: int, padding_duration: float) -> None:
        """
        Update final output details.
        
        Args:
            output_file: Path to the final output file
            format: Audio format (e.g., 'wav')
            duration: Total duration in seconds
            size_bytes: File size in bytes
            padding_duration: Total padding duration in seconds
        """
        self.data["final_output"]["file"] = os.path.basename(output_file)
        self.data["final_output"]["format"] = format
        self.data["final_output"]["total_duration"] = duration
        self.data["final_output"]["segments_count"] = len(self.data["segments"])
        self.data["final_output"]["size_bytes"] = size_bytes
        self.data["final_output"]["padding_duration"] = padding_duration
        logging.info(f"Updated final output details")

    def _update_processing_summary(self) -> None:
        """
        Update processing summary statistics.
        """
        if not self.data["segments"]:
            return
            
        # Calculate total duration
        total_duration = sum(
            segment.get("duration", 0) for segment in self.data["segments"]
        )
        
        # Calculate input duration (speech only)
        input_duration = sum(
            segment.get("input_duration", 0) for segment in self.data["segments"]
        )
        
        # Calculate average pace
        total_words = sum(
            len(segment.get("text", "").split()) for segment in self.data["segments"]
        )
        average_pace = total_words / total_duration if total_duration > 0 else 0
        
        # Calculate average segment duration
        average_segment_duration = total_duration / len(self.data["segments"])
        
        self.data["processing_summary"]["total_duration"] = total_duration
        self.data["processing_summary"]["input_duration"] = input_duration
        self.data["processing_summary"]["average_pace"] = average_pace
        self.data["processing_summary"]["average_segment_duration"] = average_segment_duration

    def save(self) -> None:
        """
        Save synthesis details to a JSON file.
        """
        try:
            # Log current state before updates
            logging.info(f"Logger save starting with data: {json.dumps(self.data, indent=2)}")
            logging.info(f"Silence padding array length: {len(self.data['silence_padding'])}")
            
            # Update processing summary with current values
            self.data["processing_summary"]["total_segments"] = len(self.data["segments"])
            self.data["processing_summary"]["total_duration"] = sum(
                segment["end_time"] - segment["start_time"] for segment in self.data["segments"]
            )
            
            # Calculate average segment duration
            if self.data["processing_summary"]["total_segments"] > 0:
                self.data["processing_summary"]["average_segment_duration"] = (
                    self.data["processing_summary"]["total_duration"] / 
                    self.data["processing_summary"]["total_segments"]
                )
            
            # Log silence padding details before calculation
            logging.info(f"Silence padding details before save: {self.data['silence_padding']}")
            
            # Update final output details with padding information
            padding_duration = sum(pad["duration"] for pad in self.data["silence_padding"])
            logging.info(f"Calculated padding duration: {padding_duration}")
            
            self.data["final_output"]["padding_duration"] = padding_duration
            self.data["processing_summary"]["padding_duration"] = padding_duration
            
            # Log final state before saving
            logging.info(f"Final data state before save: {json.dumps(self.data, indent=2)}")
            
            # Save to file
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Synthesis details saved to: {self.log_file}")
            logging.info(f"Final silence padding array length: {len(self.data['silence_padding'])}")
            
        except Exception as e:
            logging.error(f"Error saving synthesis details: {str(e)}")
            logging.error(f"Data state at error: {json.dumps(self.data, indent=2)}")
            raise

    @staticmethod
    def get_log_file_path(session_id: str, output_dir: str) -> str:
        """
        Get the path to the synthesis details file for a given session.
        
        Args:
            session_id: Session ID
            output_dir: Base output directory
            
        Returns:
            Path to the synthesis details file
        """
        synthesis_dir = os.path.join(output_dir, "synthesis")
        return os.path.join(synthesis_dir, f"synthesis_details_{session_id}.json")

    @staticmethod
    def load(session_id: str, output_dir: str) -> Dict:
        """
        Load synthesis details from a previous session.
        
        Args:
            session_id: Session ID
            output_dir: Base output directory
            
        Returns:
            Dictionary containing synthesis details
        """
        log_file = SynthesisLogger.get_log_file_path(session_id, output_dir)
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Synthesis details file not found: {log_file}")
            raise
        except Exception as e:
            logging.error(f"Error loading synthesis details: {str(e)}")
            raise
