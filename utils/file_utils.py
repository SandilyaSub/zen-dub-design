import os
import shutil
import random
import string
from pathlib import Path
from datetime import datetime
import json
import csv
import logging
import tempfile
import uuid
import warnings
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

def generate_timestamp_session_id():
    """
    Generate a session ID in the format DDMMMYY_HHMMSS with a random suffix.
    
    Returns:
        str: A formatted session ID (e.g., 30Mar25_122340_ab)
    """
    now = datetime.now()
    # Format: 30Mar25_122340
    timestamp = now.strftime("%d%b%y_%H%M%S")
    
    # Add a small random suffix to prevent collisions
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=2))
    session_id = f"{timestamp}_{random_suffix}"
    
    return session_id

def generate_random_session_id():
    """
    Generate a session ID in the format session_XXXXXXXXXX where X is a random alphanumeric character.
    This format is consistent with the session ID format used in other parts of the application.
    
    Returns:
        str: A formatted session ID (e.g., session_9fqgozf302s)
    """
    # Generate a random string of 10 lowercase letters and numbers
    random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    session_id = f"session_{random_chars}"
    
    return session_id

def ensure_dir(directory):
    """Ensure that a directory exists, creating it if necessary."""
    os.makedirs(directory, exist_ok=True)
    return directory

def get_upload_path(upload_folder, filename):
    """Generate a file path for uploaded files."""
    ensure_dir(upload_folder)
    return os.path.join(upload_folder, filename)

def get_output_path(output_folder, filename):
    """Generate a file path for output files."""
    ensure_dir(output_folder)
    return os.path.join(output_folder, filename)

def clean_files(directory, pattern=None):
    """Remove files matching a pattern from a directory."""
    if not os.path.exists(directory):
        return True
    
    if pattern:
        for file in Path(directory).glob(pattern):
            file.unlink()
    else:
        shutil.rmtree(directory)
        ensure_dir(directory)
    
    return True

def get_file_extension(filename):
    """Get the extension of a file."""
    return Path(filename).suffix.lower()

def allowed_file(filename):
    """Check if the file is an allowed audio file based on extension."""
    allowed_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']
    return get_file_extension(filename) in allowed_extensions

def create_session_directory(session_id, base_dir="outputs"):
    """
    Create a directory structure for a session.
    
    Args:
        session_id (str): The session ID
        base_dir (str): Base directory for outputs
        
    Returns:
        dict: Dictionary with paths to different subdirectories
    """
    # Create main session directory
    session_dir = os.path.join(base_dir, session_id)
    ensure_dir(session_dir)
    
    # Create subdirectories
    audio_dir = os.path.join(session_dir, "audio")
    transcription_dir = os.path.join(session_dir, "transcription")
    translation_dir = os.path.join(session_dir, "translation")
    tts_dir = os.path.join(session_dir, "tts")
    
    ensure_dir(audio_dir)
    ensure_dir(transcription_dir)
    ensure_dir(translation_dir)
    ensure_dir(tts_dir)
    
    return {
        "session_dir": session_dir,
        "audio_dir": audio_dir,
        "transcription_dir": transcription_dir,
        "translation_dir": translation_dir,
        "tts_dir": tts_dir
    }

def save_original_audio(session_id, audio_file_path, base_dir="outputs"):
    """
    Save the original audio file to the session directory.
    
    Args:
        session_id (str): The session ID
        audio_file_path (str): Path to the audio file
        base_dir (str): Base directory for outputs
        
    Returns:
        str: Path to the saved audio file
    """
    dirs = create_session_directory(session_id, base_dir)
    
    # Get file extension
    ext = get_file_extension(audio_file_path)
    
    # Destination path
    dest_path = os.path.join(dirs["audio_dir"], f"original{ext}")
    
    # Copy the file
    shutil.copy2(audio_file_path, dest_path)
    
    return dest_path

def save_diarization_data(output_dir, transcript, segments, base_dir="outputs", translated_segments=None):
    """
    Save diarization data to CSV and JSON files.
    
    Args:
        output_dir (str): The output directory path
        transcript (str): The transcription text
        segments (list): List of diarization segments
        base_dir (str): Base directory for outputs (used only if output_dir is a session_id)
        translated_segments (dict, optional): Dictionary mapping segment indices to translated text
        
    Returns:
        dict: Paths to the saved files
    """
    import csv
    import json
    
    # Check if output_dir is actually a session_id
    if not os.path.isdir(output_dir):
        session_id = output_dir
        dirs = create_session_directory(session_id, base_dir)
        output_dir = dirs["session_dir"]
    else:
        # Extract session_id from the path if it's a directory
        session_id = os.path.basename(output_dir)
    
    # Save raw JSON
    diarization_data = {
        "transcript": transcript,
        "segments": segments
    }
    
    # Add translated text to segments if available
    if translated_segments:
        for i, segment in enumerate(segments):
            if i in translated_segments:
                segment['translated_text'] = translated_segments[i]
    
    # Ensure all segments have gender information
    for segment in segments:
        if 'gender' not in segment:
            segment['gender'] = 'M'  # Default gender if not set
    
    # Save the main diarization.json file
    json_path = os.path.join(output_dir, "diarization.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(diarization_data, f, ensure_ascii=False, indent=2)
    
    # If this is being called with a session_id, also update the metadata
    # to ensure preserve_background_music and other preferences are preserved
    if session_id:
        try:
            from utils.metadata_manager import get_metadata_field
            # Get the current preserve_background_music preference
            preserve_background_music = get_metadata_field(session_id, "preserve_background_music", False)
            print(f"Retrieved preserve_background_music from metadata: {preserve_background_music}")
            
            # Re-save it to ensure it's not lost
            from utils.metadata_manager import update_metadata_field
            update_metadata_field(session_id, "preserve_background_music", preserve_background_music)
            print(f"Re-saved preserve_background_music to metadata: {preserve_background_music}")
            
            # Update source_language in metadata if available in diarization_data
            if "language_code" in diarization_data:
                update_metadata_field(session_id, "source_language", diarization_data["language_code"])
                print(f"Updated source_language in metadata: {diarization_data['language_code']}")
            
            # Get target_language from Flask session and update metadata
            try:
                from flask import session as flask_session
                if 'target_language' in flask_session:
                    target_language = flask_session.get('target_language')
                    update_metadata_field(session_id, "target_language", target_language)
                    print(f"Updated target_language in metadata from session: {target_language}")
            except ImportError:
                print("Could not import Flask session, skipping target_language update")
        except Exception as e:
            print(f"Error preserving metadata during diarization save: {str(e)}")
    
    # Save a copy of the original diarization data to tool_outputs directory
    tool_outputs_dir = os.path.join(output_dir, "tool_outputs")
    os.makedirs(tool_outputs_dir, exist_ok=True)
    
    original_json_path = os.path.join(tool_outputs_dir, "diarization_original.json")
    with open(original_json_path, 'w', encoding='utf-8') as f:
        json.dump(diarization_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved original diarization data to {original_json_path}")
    
    # If this is a translated diarization, also save it to diarization_translated.json
    if translated_segments:
        translated_json_path = os.path.join(output_dir, "diarization_translated.json")
        with open(translated_json_path, 'w', encoding='utf-8') as f:
            json.dump(diarization_data, f, ensure_ascii=False, indent=2)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "diarization.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['segment_id', 'speaker_id', 'start_time', 'end_time', 'text', 'confidence', 'translated_text', 'gender']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for i, segment in enumerate(segments):
            row = {
                'segment_id': segment.get('segment_id', i),
                'speaker_id': segment.get('speaker', 'unknown'),
                'start_time': segment.get('start_time', segment.get('start', 0)),
                'end_time': segment.get('end_time', segment.get('end', 0)),
                'text': segment.get('text', ''),
                'confidence': segment.get('confidence', 0),
                'translated_text': segment.get('translated_text', ''),
                'gender': segment.get('gender', 'M')
            }
            writer.writerow(row)
    
    return {
        "json_path": json_path,
        "csv_path": csv_path,
        "original_json_path": original_json_path
    }

def save_transcription(session_id, transcription, base_dir="outputs"):
    """
    Save transcription text to a file.
    
    Args:
        session_id (str): The session ID
        transcription (str): The transcription text
        base_dir (str): Base directory for outputs
        
    Returns:
        str: Path to the saved file
    """
    dirs = create_session_directory(session_id, base_dir)
    
    # Save text file
    text_path = os.path.join(dirs["transcription_dir"], "transcript.txt")
    with open(text_path, 'w', encoding='utf-8') as f:
        f.write(transcription)
    
    return text_path

def save_translation(session_id, source_text, target_text, source_lang, target_lang, base_dir="outputs"):
    """
    Save translation data to files.
    
    Args:
        session_id (str): The session ID
        source_text (str): The source text
        target_text (str): The translated text
        source_lang (str): Source language code
        target_lang (str): Target language code
        base_dir (str): Base directory for outputs
        
    Returns:
        dict: Paths to the saved files
    """
    dirs = create_session_directory(session_id, base_dir)
    
    # Save source text
    source_path = os.path.join(dirs["translation_dir"], f"{source_lang}.txt")
    with open(source_path, 'w', encoding='utf-8') as f:
        f.write(source_text)
    
    # Save target text
    target_path = os.path.join(dirs["translation_dir"], f"{target_lang}.txt")
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(target_text)
    
    return {
        "source_path": source_path,
        "target_path": target_path
    }

def save_synthesized_audio(session_id, audio_data, target_language, format="wav", base_dir="outputs"):
    """
    Save synthesized audio data to a single, canonical file for the session and language.
    
    Args:
        session_id (str): The session ID
        audio_data (bytes): The audio data
        target_language (str): Target language for the synthesis
        format (str): Audio format (wav, mp3)
        base_dir (str): Base directory for outputs
        
    Returns:
        str: Path to the saved file
    """
    dirs = create_session_directory(session_id, base_dir)
    # Clean up any old synthesized files in the tts_dir
    tts_dir = dirs["tts_dir"]
    for fname in os.listdir(tts_dir):
        if fname.startswith("final_output_") or fname in ["synthesized.wav", "temp.wav"]:
            try:
                os.remove(os.path.join(tts_dir, fname))
            except Exception:
                pass
    # Canonical file name
    file_name = f"final_output_{target_language.lower()}_{session_id}.{format}"
    audio_path = os.path.join(tts_dir, file_name)
    with open(audio_path, 'wb') as f:
        f.write(audio_data)
    return audio_path

def save_metadata(session_id, new_metadata, base_dir="outputs"):
    """
    Save session metadata to a JSON file, preserving existing metadata.
    
    Args:
        session_id (str): The session ID
        new_metadata (dict): New metadata to save
        base_dir (str): Base directory for outputs
        
    Returns:
        str: Path to the saved file
    """
    import json
    import logging
    
    dirs = create_session_directory(session_id, base_dir)
    metadata_path = os.path.join(dirs["session_dir"], "metadata.json")
    
    # Load existing metadata if available
    existing_metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            logging.info(f"Loaded existing metadata from {metadata_path}: {existing_metadata}")
        except Exception as e:
            logging.error(f"Error loading existing metadata: {str(e)}")
    
    # Update with new metadata
    existing_metadata.update(new_metadata)
    
    # Log the updated metadata
    logging.info(f"Saving updated metadata to {metadata_path}: {existing_metadata}")
    
    # Save updated metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
    
    return metadata_path

def update_diarization_with_translation(session_id, translation, target_lang, base_dir="outputs"):
    """
    Update diarization data with translations for each segment.
    
    Args:
        session_id (str): The session ID
        translation (str): The full translated text
        target_lang (str): Target language code
        base_dir (str): Base directory for outputs
        
    Returns:
        dict: Updated diarization data
    """
    import json
    import os
    
    # Get paths
    dirs = create_session_directory(session_id, base_dir)
    diarization_path = os.path.join(dirs["session_dir"], "diarization.json")
    
    # Check if diarization file exists
    if not os.path.exists(diarization_path):
        return None
    
    # Load diarization data
    with open(diarization_path, 'r', encoding='utf-8') as f:
        diarization_data = json.load(f)
    
    # Translate each segment individually
    segments = diarization_data.get("segments", [])
    translated_segments = {}
    
    # If we have a single translation for the entire transcript,
    # we need to split it up for each segment based on relative length
    if segments:
        # Simple approach: distribute translation based on relative text length
        total_source_length = sum(len(segment.get('text', '')) for segment in segments)
        
        if total_source_length > 0:
            start_idx = 0
            for i, segment in enumerate(segments):
                segment_text = segment.get('text', '')
                segment_length = len(segment_text)
                
                # Calculate relative length and corresponding portion of translation
                if segment_length > 0:
                    relative_length = segment_length / total_source_length
                    segment_translation_length = max(1, int(len(translation) * relative_length))
                    
                    # Extract portion of translation for this segment
                    end_idx = min(start_idx + segment_translation_length, len(translation))
                    segment_translation = translation[start_idx:end_idx].strip()
                    
                    # Store translated text
                    translated_segments[i] = segment_translation
                    start_idx = end_idx
    
    # Update diarization data with translations
    save_diarization_data(
        dirs["session_dir"],
        diarization_data.get("transcript", ""),
        segments,
        base_dir,
        translated_segments
    )
    
    return {
        "diarization_data": diarization_data,
        "translated_segments": translated_segments
    }

def save_diarization_with_translations(output_dir, diarization_data, translated_segments, base_dir="outputs", target_language=None):
    """
    Save diarization data with translations to new JSON and CSV files.
    
    Args:
        output_dir (str): The output directory path
        diarization_data (dict): Original diarization data
        translated_segments (dict): Dictionary mapping segment indices to translated text
        base_dir (str): Base directory for outputs
        target_language (str, optional): Target language for translation
        
    Returns:
        dict: Paths to the saved files
    """
    import csv
    import json
    import os
    import logging
    
    # Check if output_dir is actually a session_id
    if not os.path.isdir(output_dir):
        session_id = output_dir
        dirs = create_session_directory(session_id, base_dir)
        output_dir = dirs["session_dir"]
    else:
        # Extract session_id from the path if it's a directory
        session_id = os.path.basename(output_dir)
    
    # Create a deep copy of the diarization data to avoid modifying the original
    import copy
    translated_data = copy.deepcopy(diarization_data)
    
    # Add target language to the translated data if provided
    if target_language:
        translated_data['target_language'] = target_language
        logging.info(f"Setting target language in translated data: {target_language}")
    
    # Clean diarization data while preserving important information
    processed_segments = set()
    speaker_gender_map = {}
    cleaned_segments = []
    
    for i, segment in enumerate(translated_data['segments']):
        # Create unique segment identifier using either start/end or start_time/end_time
        start_time = segment.get('start_time', segment.get('start', 0))
        end_time = segment.get('end_time', segment.get('end', 0))
        segment_id = segment.get('segment_id', f"segment_{i:03d}")
        unique_id = f"{start_time:.2f}_{end_time:.2f}_{segment.get('text', '')}"
        
        if unique_id not in processed_segments:
            # Update speaker gender map
            if segment.get('gender'):
                speaker_gender_map[segment.get('speaker', 'SPEAKER_00')] = segment['gender']
            
            # Create cleaned segment with consistent key names
            cleaned_segment = {
                'start_time': start_time,  # Keep only start_time/end_time
                'end_time': end_time,      # Remove redundant start/end
                'segment_id': segment_id,  # Include segment_id
                'text': segment.get('text', ''),  # Preserve original text
                'speaker': segment.get('speaker', 'SPEAKER_00'),
                'gender': segment.get('gender', speaker_gender_map.get(segment.get('speaker', 'SPEAKER_00'), 'unknown'))
            }
            
            # Preserve the translated_text if it exists in the original segment
            if 'translated_text' in segment:
                cleaned_segment['translated_text'] = segment['translated_text']
            
            # Add language to segment if target_language is provided
            if target_language:
                cleaned_segment['language'] = target_language
            
            cleaned_segments.append(cleaned_segment)
            processed_segments.add(unique_id)
    
    # Sort segments to maintain chronological order
    cleaned_segments.sort(key=lambda x: x['start_time'])
    
    # Replace original segments with cleaned ones
    translated_data['segments'] = cleaned_segments
    
    # Add segment_id to the transcript object itself
    if 'transcript' in translated_data and cleaned_segments:
        translated_data['segment_id'] = cleaned_segments[0].get('segment_id', 'seg_000')
    
    # Add translations to segments from the translated_segments dictionary
    segments = translated_data.get("segments", [])
    for segment_id, translated_text in translated_segments.items():
        # Find the segment by ID or index
        if isinstance(segment_id, str):
            # Try to find segment by ID
            for segment in segments:
                if segment.get('segment_id') == segment_id:
                    segment['translated_text'] = translated_text
                    break
        elif isinstance(segment_id, int) and segment_id < len(segments):
            # Use index-based lookup
            segments[segment_id]['translated_text'] = translated_text
    
    # Ensure all segments have a translated_text field
    for segment in segments:
        if not segment.get('translated_text'):
            logging.warning(f"Empty translated_text for segment {segment.get('segment_id', 'unknown')}, using original text as fallback")
            segment['translated_text'] = segment.get('text', '')
    
    # Create new file paths for translated data
    json_path = os.path.join(output_dir, "diarization_translated.json")
    csv_path = os.path.join(output_dir, "diarization_translated.csv")
    
    # Save JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    
    # If this is being called with a session_id, also update the metadata
    # to ensure preserve_background_music and other preferences are preserved
    if session_id:
        try:
            from utils.metadata_manager import get_metadata_field
            # Get the current preserve_background_music preference
            preserve_background_music = get_metadata_field(session_id, "preserve_background_music", False)
            print(f"Retrieved preserve_background_music from metadata during translation: {preserve_background_music}")
            
            # Re-save it to ensure it's not lost
            from utils.metadata_manager import update_metadata_field
            update_metadata_field(session_id, "preserve_background_music", preserve_background_music)
            print(f"Re-saved preserve_background_music to metadata during translation: {preserve_background_music}")
            
            # Update source_language in metadata if available in diarization_data
            if "language_code" in translated_data:
                update_metadata_field(session_id, "source_language", translated_data["language_code"])
                print(f"Updated source_language in metadata: {translated_data['language_code']}")
            
            # Get target_language from Flask session and update metadata
            try:
                from flask import session as flask_session
                if 'target_language' in flask_session:
                    target_language = flask_session.get('target_language')
                    update_metadata_field(session_id, "target_language", target_language)
                    print(f"Updated target_language in metadata from session: {target_language}")
            except ImportError:
                print("Could not import Flask session, skipping target_language update")
        except Exception as e:
            print(f"Error preserving metadata during translation save: {str(e)}")
    
    # Save a copy of the original translated diarization data to tool_outputs directory
    tool_outputs_dir = os.path.join(output_dir, "tool_outputs")
    os.makedirs(tool_outputs_dir, exist_ok=True)
    
    original_translated_json_path = os.path.join(tool_outputs_dir, "diarization_translated_original.json")
    with open(original_translated_json_path, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    
    print(f"Saved original translated diarization data to {original_translated_json_path}")
    
    # Save CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['segment_id', 'start_time', 'end_time', 'speaker', 'gender', 'text', 'translated_text'])
        
        # Write rows
        for segment in segments:
            writer.writerow([
                segment.get('segment_id', ''),
                segment.get('start_time', 0),
                segment.get('end_time', 0),
                segment.get('speaker', 'SPEAKER_00'),
                segment.get('gender', 'unknown'),
                segment.get('text', ''),
                segment.get('translated_text', '')
            ])
    
    # Return paths to the saved files
    return {
        "json": json_path,
        "csv": csv_path,
        "original_translated_json": original_translated_json_path
    }

def translate_and_save_diarization(session_id, target_language, base_dir="outputs"):
    """
    Translate diarization data and save both diarized and concatenated translations.
    
    Args:
        session_id: Session ID
        target_language: Target language for translation
        base_dir: Base directory for outputs
        
    Returns:
        dict: Results including paths to saved files
    """
    from modules.google_translation import translate_diarized_content, LANGUAGE_MAP
    import json
    import os
    import logging
    import traceback
    
    # Add explicit debug logging
    print(f"==== TRANSLATION UTIL DEBUG ==== Starting translate_and_save_diarization for session_id={session_id}, target_language={target_language}")
    
    # Get paths
    dirs = create_session_directory(session_id, base_dir)
    print(f"==== TRANSLATION UTIL DEBUG ==== Created session directory: {dirs['session_dir']}")
    
    # First check in the transcription directory (new expected location)
    diarization_path = os.path.join(dirs["session_dir"], "diarization.json")
    
    # If not found, check in the session root directory (current actual location)
    if not os.path.exists(diarization_path):
        print(f"==== TRANSLATION UTIL DEBUG ==== Diarization file not found at: {diarization_path}")
        diarization_path = os.path.join(dirs["session_dir"], "diarization.json")
        print(f"==== TRANSLATION UTIL DEBUG ==== Checking alternative path: {diarization_path}")
        
    # Check if diarization file exists
    if not os.path.exists(diarization_path):
        error_msg = f"Diarization file not found: {diarization_path}"
        print(f"==== TRANSLATION UTIL DEBUG ==== Error: {error_msg}")
        raise FileNotFoundError(error_msg)
    
    print(f"==== TRANSLATION UTIL DEBUG ==== Found diarization file at: {diarization_path}")
    
    # Load diarization data
    try:
        with open(diarization_path, 'r', encoding='utf-8') as f:
            diarization_data = json.load(f)
        print(f"==== TRANSLATION UTIL DEBUG ==== Successfully loaded diarization data with {len(diarization_data.get('segments', []))} segments")
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse diarization.json: {str(e)}"
        print(f"==== TRANSLATION UTIL DEBUG ==== JSON Error: {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Error loading diarization data: {str(e)}"
        print(f"==== TRANSLATION UTIL DEBUG ==== Error: {error_msg}")
        raise
    
    # Get source language from diarization data, metadata, or detect it
    source_language = None
    
    # First try to get language from diarization data
    if "language_code" in diarization_data:
        # Map Sarvam language codes to our standard format
        # Create a reverse mapping from Sarvam codes to our standard language names
        reverse_language_map = {
            "hi-in": "hindi",
            "en-in": "english",
            "ta-in": "tamil",
            "te-in": "telugu",
            "kn-in": "kannada",
            "ml-in": "malayalam",
            "bn-in": "bengali",
            "mr-in": "marathi",
            "gu-in": "gujarati",
            "pa-in": "punjabi",
            "or-in": "odia",
            "ur-in": "urdu",
            # Add short codes as well
            "hi": "hindi",
            "en": "english",
            "ta": "tamil",
            "te": "telugu",
            "kn": "kannada",
            "ml": "malayalam",
            "bn": "bengali",
            "mr": "marathi",
            "gu": "gujarati",
            "pa": "punjabi",
            "or": "odia",
            "ur": "urdu"
        }
        
        lang_code = diarization_data.get("language_code", "").lower()
        source_language = reverse_language_map.get(lang_code)
        print(f"==== TRANSLATION UTIL DEBUG ==== Using language from diarization data: {lang_code} -> {source_language}")
        logging.info(f"Using language from diarization data: {lang_code} -> {source_language}")
    
    # If not found in diarization data, check metadata
    if not source_language:
        metadata_path = os.path.join(dirs["session_dir"], "metadata.json")
        print(f"==== TRANSLATION UTIL DEBUG ==== Checking metadata at: {metadata_path}")
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    source_language = metadata.get("source_language")
                    if source_language:
                        print(f"==== TRANSLATION UTIL DEBUG ==== Using language from metadata: {source_language}")
                        logging.info(f"Using language from metadata: {source_language}")
            except Exception as e:
                print(f"==== TRANSLATION UTIL DEBUG ==== Error reading metadata: {str(e)}")
    
    # If still not found, use a default but log a warning
    if not source_language:
        # Check if there's transcript text to make a better guess
        if "transcript" in diarization_data and diarization_data["transcript"]:
            # Simple script-based detection for common Indian languages
            text = diarization_data["transcript"]
            print(f"==== TRANSLATION UTIL DEBUG ==== Detecting language from transcript: {text[:50]}...")
            
            # Check for Telugu script
            if any(ord(char) >= 0x0C00 and ord(char) <= 0x0C7F for char in text):
                source_language = "telugu"
                print("==== TRANSLATION UTIL DEBUG ==== Detected Telugu script in transcript")
                logging.info("Detected Telugu script in transcript")
            # Check for Hindi/Devanagari script
            elif any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in text):
                source_language = "hindi"
                print("==== TRANSLATION UTIL DEBUG ==== Detected Hindi script in transcript")
                logging.info("Detected Hindi script in transcript")
            # Check for Tamil script
            elif any(ord(char) >= 0x0B80 and ord(char) <= 0x0BFF for char in text):
                source_language = "tamil"
                print("==== TRANSLATION UTIL DEBUG ==== Detected Tamil script in transcript")
                logging.info("Detected Tamil script in transcript")
            # Check for Kannada script
            elif any(ord(char) >= 0x0C80 and ord(char) <= 0x0CFF for char in text):
                source_language = "kannada"
                print("==== TRANSLATION UTIL DEBUG ==== Detected Kannada script in transcript")
                logging.info("Detected Kannada script in transcript")
            # Check for Malayalam script
            elif any(ord(char) >= 0x0D00 and ord(char) <= 0x0D7F for char in text):
                source_language = "malayalam"
                print("==== TRANSLATION UTIL DEBUG ==== Detected Malayalam script in transcript")
                logging.info("Detected Malayalam script in transcript")
            # Check for Bengali script
            elif any(ord(char) >= 0x0980 and ord(char) <= 0x09FF for char in text):
                source_language = "bengali"
                print("==== TRANSLATION UTIL DEBUG ==== Detected Bengali script in transcript")
                logging.info("Detected Bengali script in transcript")
            else:
                source_language = "english"
                print("==== TRANSLATION UTIL DEBUG ==== No Indic scripts detected, defaulting to English")
                logging.info("No Indic scripts detected, defaulting to English")
        else:
            source_language = "english"
            print("==== TRANSLATION UTIL DEBUG ==== No language information found, defaulting to English")
            logging.warning("No language information found, defaulting to English")
    
    # Translate diarized content
    print(f"==== TRANSLATION UTIL DEBUG ==== Translating from {source_language} to {target_language}")
    logging.info(f"Translating from {source_language} to {target_language}")
    
    try:
        # IMPROVED ERROR HANDLING: Wrap the translation call in a try-except block
        try:
            # Directly translate the entire diarization data structure
            # This is the improved approach that matches test_gemini_api.py
            print(f"==== TRANSLATION UTIL DEBUG ==== About to call translate_diarized_content with source_language={source_language}, target_language={target_language}")
            logging.info(f"Calling translate_diarized_content with source_language={source_language}, target_language={target_language}")
            
            # Check if GEMINI_API_KEY is available
            import os
            gemini_api_key = os.environ.get("GEMINI_API_KEY")
            print(f"==== TRANSLATION UTIL DEBUG ==== GEMINI_API_KEY available: {bool(gemini_api_key)}")
            
            # Import the module directly here to check for any import errors
            try:
                from modules.google_translation import translate_diarized_content
                print("==== TRANSLATION UTIL DEBUG ==== Successfully imported translate_diarized_content")
            except ImportError as e:
                print(f"==== TRANSLATION UTIL DEBUG ==== Error importing translate_diarized_content: {str(e)}")
                raise
            
            translated_result = translate_diarized_content(diarization_data, target_language, source_language)
            print("==== TRANSLATION UTIL DEBUG ==== translate_diarized_content call completed")
            
            # IMPROVED VALIDATION: Validate the translated result
            if not isinstance(translated_result, dict):
                error_msg = f"Translation failed: Expected dict result, got {type(translated_result)}"
                print(f"==== TRANSLATION UTIL DEBUG ==== Error: {error_msg}")
                raise ValueError(error_msg)
                
            if "segments" not in translated_result or not isinstance(translated_result["segments"], list):
                error_msg = f"Translation failed: Missing or invalid 'segments' in result"
                print(f"==== TRANSLATION UTIL DEBUG ==== Error: {error_msg}")
                raise ValueError(error_msg)
                
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors specifically
            error_msg = f"Translation failed: Invalid JSON in response: {str(e)}"
            print(f"==== TRANSLATION UTIL DEBUG ==== JSON parsing error: {error_msg}")
            print(f"==== TRANSLATION UTIL DEBUG ==== Traceback: {traceback.format_exc()}")
            logging.error(f"JSON parsing error in translation: {str(e)}")
            raise ValueError(error_msg)
            
        except Exception as e:
            error_msg = f"Translation failed: {str(e)}"
            print(f"==== TRANSLATION UTIL DEBUG ==== Error in translation API: {error_msg}")
            print(f"==== TRANSLATION UTIL DEBUG ==== Traceback: {traceback.format_exc()}")
            logging.error(f"Error in translation API: {str(e)}")
            raise ValueError(error_msg)
        
        if not translated_result:
            error_msg = "Translation failed: No result returned"
            print(f"==== TRANSLATION UTIL DEBUG ==== Error: {error_msg}")
            logging.error(error_msg)
            return {
                "diarization_data": diarization_data,
                "translated_segments": {},
                "success": False,
                "error": error_msg
            }
        
        # Extract the translated segments
        translated_segments = {}
        
        # Create a mapping from original segments to translated segments
        print(f"==== TRANSLATION UTIL DEBUG ==== Processing {len(diarization_data.get('segments', []))} segments")
        for i, orig_segment in enumerate(diarization_data.get("segments", [])):
            if i < len(translated_result.get("segments", [])):
                # Get the translated text from the result
                translated_text = translated_result["segments"][i].get("translated_text", "")
                if not translated_text and "text" in translated_result["segments"][i]:
                    # Fallback: if translated_text is missing but text is present, use that
                    # (This handles the case where the model didn't follow instructions)
                    translated_text = translated_result["segments"][i].get("text", "")
                
                # Store by segment_id if available, otherwise by index
                segment_id = orig_segment.get("segment_id", str(i))
                translated_segments[segment_id] = translated_text
                
                # Directly add the translated_text to the original segment
                orig_segment["translated_text"] = translated_text
        
        # Add the full translated transcript to the diarization data
        diarization_data["translated_transcript"] = translated_result.get("transcript", "")
        
        # Add target language to the diarization data
        diarization_data["target_language"] = target_language
        
        # Save concatenated translation to translation directory
        concatenated_translation = translated_result.get("transcript", "")
        translation_path = os.path.join(dirs["translation_dir"], f"{target_language}.txt")
        print(f"==== TRANSLATION UTIL DEBUG ==== Saving translation to: {translation_path}")
        with open(translation_path, "w", encoding="utf-8") as f:
            f.write(concatenated_translation)
        
        # IMPROVED ERROR HANDLING: Wrap the save operation in a try-except block
        try:
            # Save diarization with translations
            print("==== TRANSLATION UTIL DEBUG ==== Calling save_diarization_with_translations")
            translated_files = save_diarization_with_translations(
                dirs["session_dir"],  # Save in the session directory
                diarization_data,
                translated_segments,
                base_dir,
                target_language
            )
            print(f"==== TRANSLATION UTIL DEBUG ==== save_diarization_with_translations returned: {translated_files}")
            
            # Save concatenated translation to translation directory for backward compatibility
            compat_path = os.path.join(dirs["session_dir"], f"{target_language}.txt")
            print(f"==== TRANSLATION UTIL DEBUG ==== Saving compatibility translation to: {compat_path}")
            with open(compat_path, "w", encoding="utf-8") as f:
                f.write(concatenated_translation)
            
            # Generate merged segments for better TTS alignment
            try:
                print("==== TRANSLATION UTIL DEBUG ==== Generating merged segments for better TTS alignment")
                from modules.segment_merger import merge_segments
                
                # Get the translated segments from diarization data
                segments = diarization_data.get('segments', [])
                
                if segments:
                    # Merge segments with hardcoded silence threshold
                    merged_segments = merge_segments(segments, max_silence_ms=500)
                    
                    # Create new merged data structure
                    merged_data = {
                        'transcript': diarization_data.get('transcript', ''),
                        'translated_transcript': diarization_data.get('translated_transcript', ''),
                        'merged_segments': merged_segments,
                        'original_segment_count': len(segments),
                        'merged_segment_count': len(merged_segments),
                        'max_silence_ms': 500
                    }
                    
                    # Save merged data
                    merged_file = os.path.join(dirs["session_dir"], 'diarization_translated_merged.json')
                    with open(merged_file, 'w') as f:
                        json.dump(merged_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"==== TRANSLATION UTIL DEBUG ==== Successfully merged {len(segments)} segments into {len(merged_segments)} segments")
                    
                    # Add merged file to the result
                    translated_files['diarization_translated_merged'] = merged_file
                else:
                    print("==== TRANSLATION UTIL DEBUG ==== No segments to merge")
            except Exception as merge_error:
                print(f"==== TRANSLATION UTIL DEBUG ==== Error generating merged segments: {str(merge_error)}")
                print(f"==== TRANSLATION UTIL DEBUG ==== Traceback: {traceback.format_exc()}")
                logging.error(f"Error generating merged segments: {str(merge_error)}")
                # Continue without merged segments
            
            print("==== TRANSLATION UTIL DEBUG ==== Translation process completed successfully")
            return {
                "diarization_data": diarization_data,
                "translated_segments": translated_segments,
                "translation_path": translation_path,
                "translated_files": translated_files,
                "success": True
            }
        except Exception as save_error:
            error_msg = f"Error saving translation results: {str(save_error)}"
            print(f"==== TRANSLATION UTIL DEBUG ==== {error_msg}")
            print(f"==== TRANSLATION UTIL DEBUG ==== Traceback: {traceback.format_exc()}")
            logging.error(error_msg)
            return {
                "diarization_data": diarization_data,
                "translated_segments": translated_segments,
                "success": False,
                "error": error_msg
            }
            
    except Exception as e:
        error_msg = f"Error in diarization translation: {str(e)}"
        print(f"==== TRANSLATION UTIL DEBUG ==== {error_msg}")
        print(f"==== TRANSLATION UTIL DEBUG ==== Traceback: {traceback.format_exc()}")
        logging.error(error_msg)
        # Return partial results if available
        return {
            "diarization_data": diarization_data,
            "translated_segments": {},
            "success": False,
            "error": error_msg
        }

def get_ffmpeg_path():
    """
    Get the path to the FFmpeg executable.
    
    Returns:
        str: Path to FFmpeg executable
    """
    try:
        # First try to use imageio_ffmpeg
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info(f"Using FFmpeg from imageio_ffmpeg: {ffmpeg_path}")
        return ffmpeg_path
    except ImportError:
        # If imageio_ffmpeg is not available, try to find ffmpeg in PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            logger.info(f"Using FFmpeg from PATH: {ffmpeg_path}")
            return ffmpeg_path
        else:
            # Default fallback paths
            for path in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg"]:
                if os.path.exists(path):
                    logger.info(f"Using FFmpeg from: {path}")
                    return path
            
            logger.error("FFmpeg not found. Audio processing may not work correctly.")
            return "ffmpeg"  # Return default command name as last resort
