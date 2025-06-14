import os
import warnings

# Suppress NNPACK warnings
os.environ["NNPACK_IGNORE_INCOMPATIBLE_CPU"] = "1"
os.environ["USE_NNPACK"] = "0"

# Ensure ffmpeg and ffprobe are in PATH for all subprocesses
homebrew_bin = "/opt/homebrew/bin"
if homebrew_bin not in os.environ.get("PATH", ""):
    os.environ["PATH"] = f"{homebrew_bin}:{os.environ.get('PATH', '')}"

import json
import uuid
import asyncio
import traceback
from flask import Flask, render_template, request, jsonify, session, send_from_directory, url_for, send_file
from datetime import datetime

# Dictionary to store processing status for each session
processing_status = {}
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
# datetime already imported above
import shutil
import requests
from flask_cors import CORS
from modules.audio_separator import separate_vocals_from_background, analyze_audio_components

# Filter PyTorch NNPACK warnings - multiple approaches for maximum suppression
warnings.filterwarnings("ignore", message="Could not initialize NNPACK")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# Load modules
from modules.speech_recognition import detect_language as detect_audio_language, transcribe_audio
from modules.translation import translate_text as legacy_translate_text
from modules.speech_synthesis import synthesize_speech as legacy_synthesize_speech
from modules.validation import (
    calculate_similarity, validate_translation, 
    compute_transcription_edit, compute_translation_edit, 
    compute_speaker_change_accuracy, compute_composite_metric, 
    save_validation_results, validate_translation_with_metrics
)

# Load new Sarvam and Cartesia modules
from modules.sarvam_speech import transcribe_with_vad_diarization
from modules.sarvam_translation import translate_text as sarvam_translate_text
from modules.google_translation import translate_text as google_translate_text
from modules.tts_router import synthesize_speech, get_available_voices
from modules.speech_config import get_vad_config, get_diarization_config

# Load utilities
from utils.file_utils import (
    ensure_dir, get_upload_path, get_output_path, allowed_file,
    generate_timestamp_session_id, generate_random_session_id, create_session_directory,
    save_original_audio, save_diarization_data, save_transcription,
    save_translation, save_synthesized_audio, save_metadata,
    update_diarization_with_translation, translate_and_save_diarization
)
from utils.metadata_manager import update_metadata, update_metadata_field, get_metadata_field, get_metadata, update_metadata_section, debug_metadata_changes
from utils.audio_utils import convert_audio_format
from utils.video_utils import extract_audio_from_url, is_valid_video_url

# Load environment variables
load_dotenv()

# Import secret manager utility
from utils.secret_manager import get_secret

# Get API keys from environment variables or Secret Manager
SARVAM_API_KEY = get_secret('sarvam-api-key', project_id="phonic-bivouac-272213")
if SARVAM_API_KEY:
    print(f"SARVAM_API_KEY found and loaded successfully")
else:
    print("Warning: SARVAM_API_KEY not found in environment variables or Secret Manager")

# Check for Gemini API key
GEMINI_API_KEY = get_secret('gemini-api-key', project_id="phonic-bivouac-272213")
if GEMINI_API_KEY:
    print(f"GEMINI_API_KEY found and loaded successfully")
else:
    print("Warning: GEMINI_API_KEY not found in environment variables or Secret Manager")
    
# Check for Cartesia API key
CARTESIA_API_KEY = get_secret('cartesia-api-key', project_id="phonic-bivouac-272213")
if CARTESIA_API_KEY:
    print(f"CARTESIA_API_KEY found and loaded successfully")
else:
    print("Warning: CARTESIA_API_KEY not found in environment variables or Secret Manager")

# Set Flask environment variables
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Initialize Flask app
app = Flask(__name__, 
            static_folder='app/static',
            template_folder='app/templates')

# Configure app
app.secret_key = os.environ.get('SECRET_KEY', 'indic-translator-secret-key')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['OUTPUT_FOLDER'] = os.environ.get('OUTPUT_FOLDER', 'outputs')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['SERVER_NAME'] = None  # Allow all hostnames

# Enable CORS with more explicit configuration
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Ensure upload and output directories exist
ensure_dir(app.config['UPLOAD_FOLDER'])
ensure_dir(app.config['OUTPUT_FOLDER'])

# Function to update processing status
def update_processing_status(session_id, stage, message, progress=0):
    """
    Update processing status for the frontend
    
    Args:
        session_id: Unique session identifier
        stage: Current processing stage (e.g., 'video_processing', 'transcription')
        message: User-friendly status message
        progress: Progress percentage (0-100)
    """
    if not session_id:
        return
        
    processing_status[session_id] = {
        "stage": stage,
        "message": message,
        "progress": progress,
        "timestamp": datetime.now().isoformat()
    }
    print(f"Status update for {session_id}: {stage} - {message} ({progress}%)")

# API endpoint to get processing status
@app.route('/api/processing_status/<session_id>', methods=['GET'])
def get_processing_status(session_id):
    """
    Get current processing status for a session
    """
    if not session_id or session_id not in processing_status:
        return jsonify({
            "stage": "initializing",
            "message": "Starting process...",
            "progress": 0,
            "timestamp": datetime.now().isoformat()
        })
        
    return jsonify(processing_status[session_id])

# Helper function to save original tool outputs
def save_original_output(session_id, file_name, data):
    """Save a copy of the original tool output."""
    # Create tool_outputs directory if it doesn't exist
    tool_outputs_dir = os.path.join('outputs', session_id, 'tool_outputs')
    os.makedirs(tool_outputs_dir, exist_ok=True)
    
    # Save the data to the tool_outputs directory
    output_path = os.path.join(tool_outputs_dir, file_name)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved original tool output to {output_path}")
    return output_path

@app.route('/')
def index():
    """Render the main page."""
    # Define supported languages
    output_languages = ["hindi", "english", "telugu", "tamil", "kannada", "gujarati", "marathi", "bengali", "odia", "punjabi", "malayalam"]
    
    # Get available voices for TTS
    voices = get_available_voices()
    
    return render_template('index.html', 
                          output_languages=output_languages,
                          voices=voices)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle file upload."""
    try:
        # Check if file is in request
        if 'audio' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['audio']
        
        # Check if file is empty
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Check if file is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Get session ID from request
        session_id = request.form.get('session_id')
        print(f"Received session_id: {session_id}")
        
        # Generate a unique filename
        filename = secure_filename(file.filename)
        
        # Use random-based session ID if none provided (for consistency with YouTube flow)
        if not session_id:
            session_id = generate_random_session_id()
            print(f"Generated random session_id: {session_id}")
        
        base, ext = os.path.splitext(filename)
        unique_filename = f"{session_id}{ext}"

        # Create session directories and get audio dir
        dirs = create_session_directory(session_id, base_dir="outputs")
        audio_dir = dirs["audio_dir"]
        os.makedirs(audio_dir, exist_ok=True)
        upload_path = os.path.join(audio_dir, unique_filename)

        # Save the file and verify it exists
        file.save(upload_path)
        
        if not os.path.exists(upload_path):
            return jsonify({'error': f'Failed to save file to {upload_path}'}), 500
        
        print(f"File saved successfully at: {upload_path} (Size: {os.path.getsize(upload_path)} bytes)")
        
        # Convert to WAV if needed
        if ext.lower() != '.wav':
            wav_filename = f"{session_id}.wav"
            wav_path = os.path.join(audio_dir, wav_filename)
            try:
                convert_audio_format(upload_path, wav_path)
                upload_path = wav_path
                print(f"Successfully converted to WAV: {wav_path}")
            except Exception as e:
                print(f"Error converting audio format: {str(e)}")
                print(f"Using original file format instead: {upload_path}")
                # Continue with the original file format
        
        # Store file path in session
        session['upload_path'] = upload_path
        session['session_id'] = session_id
        
        # Clear any existing transcription data to ensure fresh processing
        session.pop('transcription', None)
        session.pop('diarization', None)
        session.pop('source_language', None)
        session.pop('translation', None)
        
        # Get additional parameters
        num_speakers = int(request.form.get('num_speakers', 1))
        speaker_genders = request.form.get('speaker_genders', 'M').split(',')
        target_language = request.form.get('target_language', 'hindi')
        
        # Store parameters in session
        session['num_speakers'] = num_speakers
        session['speaker_genders'] = speaker_genders
        session['target_language'] = target_language
        
        # Save original audio to session directory (already saved above)
        try:
            # No need to copy, just use upload_path
            saved_path = upload_path
            # Save initial metadata
            metadata = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "original_filename": filename,
                "num_speakers": num_speakers,
                "speaker_genders": speaker_genders,
                "target_language": target_language
            }
            # Use the new metadata manager to update metadata
            update_metadata(session_id, metadata)
            print(f"Original audio saved to session directory: {saved_path}")
            
            # Initialize debug logging for this session
            debug_logger = debug_metadata_changes(session_id)
            debug_logger.info(f"Starting new session: {session_id}")
            
            # Separate vocals from background music
            try:
                print(f"Starting audio separation for session: {session_id}")
                separation_result = separate_vocals_from_background(
                    input_file=upload_path,
                    output_dir="outputs",
                    session_id=session_id
                )
                
                # Add separation results to metadata
                audio_separation_data = {
                    "vocals_path": separation_result["vocals_path"],
                    "background_path": separation_result["background_path"],
                    "has_significant_background": separation_result["has_significant_background"]
                }
                # Use the metadata manager to update just the audio_separation section
                update_metadata_section(session_id, "audio_separation", audio_separation_data)
                
                print(f"Audio separation complete. Background music saved to: {separation_result['background_path']}")
                if separation_result["has_significant_background"]:
                    print(f"Significant background music detected in the audio")
                else:
                    print(f"No significant background music detected in the audio")
                    
            except Exception as e:
                print(f"Error during audio separation: {str(e)}")
                print("Continuing with original audio file")
                # Continue with the original audio file if separation fails
        except Exception as e:
            print(f"Error saving to session directory: {str(e)}")
        
        print(f"File uploaded successfully. Path: {upload_path}, Session ID: {session_id}")
        
        return jsonify({
            'success': True,
            'filename': os.path.basename(upload_path),
            'upload_path': upload_path,
            'session_id': session_id
        })
        
    except Exception as e:
        import traceback
        print(f"Error in upload_file: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/record', methods=['POST'])
def record_audio():
    """Handle audio recording."""
    try:
        # Check if file is in request
        if 'audio' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['audio']
        
        # Generate a unique filename
        unique_id = str(uuid.uuid4())
        filename = f"recording_{unique_id}.wav"
        
        # Save the file
        upload_path = get_upload_path(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        
        # Store file path in session
        session['upload_path'] = upload_path
        
        # Get additional parameters
        num_speakers = int(request.form.get('num_speakers', 1))
        speaker_genders = request.form.get('speaker_genders', 'M').split(',')
        target_language = request.form.get('target_language', 'hindi')
        
        # Store parameters in session
        session['num_speakers'] = num_speakers
        session['speaker_genders'] = speaker_genders
        session['target_language'] = target_language
        
        return jsonify({
            'success': True,
            'filename': filename,
            'upload_path': upload_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/detect_language', methods=['POST'])
def detect_language():
    """Detect language and transcribe audio file with diarization."""
    try:
        # Log request data for debugging
        print(f"Request JSON: {request.json}")
        print(f"Request Form: {request.form}")
        print(f"Session data: {session}")
        
        # Get session ID from request
        session_id = request.json.get('session_id')
        if not session_id:
            print("Error: No session_id provided in request")
            return jsonify({'error': 'No session ID provided'}), 400
            
        print(f"Requested session_id: {session_id}")
        
        # Look for the file based on session_id
        potential_file_paths = [
            get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.wav"),
            get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.mp3"),
            get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.webm"),
            get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.ogg")
        ]
        
        upload_path = None
        for path in potential_file_paths:
            if os.path.exists(path):
                upload_path = path
                break
                
        if not upload_path:
            print(f"Error: No audio file found for session {session_id}")
            print(f"Checked paths: {potential_file_paths}")
            return jsonify({'error': 'No audio file found for this session'}), 400
            
        print(f"Found audio file at: {upload_path}")
        
        # Check if API key is available
        if not SARVAM_API_KEY:
            print("Error: SARVAM_API_KEY not found in environment variables")
            return jsonify({'error': 'Speech recognition service is not configured properly'}), 500
        
        # Create output directory for VAD segments
        vad_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id, "vad_segments")
        ensure_dir(vad_output_dir)
        
        # Get VAD and diarization configurations
        vad_config = get_vad_config()
        
        print(f"Using VAD with threshold: {vad_config['threshold']}, combine_duration: {vad_config['combine_duration']}s")
            
        # Use asyncio to run the async transcribe_with_vad_diarization function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Use the new VAD-enhanced diarization function
            result = loop.run_until_complete(
                transcribe_with_vad_diarization(
                    audio_path=upload_path,
                    api_key=SARVAM_API_KEY,
                    vad_segments_dir=vad_output_dir,
                    min_segment_duration=vad_config.get('min_segment_duration', 1.0)
                )
            )
            loop.close()
            
            # Check for errors in the result
            if 'error' in result:
                error_message = result.get('error', 'Failed to process audio')
                print(f"Error in transcribe_with_vad_diarization: {error_message}")
                
                # If we have previous transcription results in the session, use those
                if 'transcription' in session:
                    print(f"Using existing transcription from session: {session['transcription'][:50]}...")
                    return jsonify({
                        'success': True,
                        'message': 'Using existing transcription due to API error',
                        'language': session.get('source_language', 'unknown'),
                        'transcription': session.get('transcription', ''),
                        'diarization': session.get('diarization', {'segments': [], 'speakers': {}})
                    })
                
                return jsonify({'error': error_message}), 500
            
            # Process successful result
            language_code = result.get('language_code', 'hi-IN')  # Default to Hindi if not detected
            transcript = result.get('transcript', '')
            segments = result.get('segments', [])
            
            # Map language codes to display names
            language_map = {
                'hi-IN': 'hindi',
                'te-IN': 'telugu',
                'ta-IN': 'tamil',
                'kn-IN': 'kannada',
                'ml-IN': 'malayalam',
                'bn-IN': 'bengali',
                'en-IN': 'english'
            }
            
            display_language = language_map.get(language_code, language_code)
            
            # Process speakers
            speakers = {}
            for i, segment in enumerate(segments):
                speaker_id = segment.get('speaker', f'SPEAKER_{i}')
                if speaker_id not in speakers:
                    speakers[speaker_id] = {
                        'id': speaker_id,
                        'gender': 'M',  # Default gender
                        'segments': []
                    }
                
                # Propagate gender to segment
                segment['gender'] = speakers[speaker_id]['gender']
                
                speakers[speaker_id]['segments'].append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', '')
                })
            
            # Save results to session
            session['transcription'] = transcript
            session['source_language'] = language_code
            session['target_language'] = display_language
            session['diarization'] = {
                'segments': segments
            }
            session['num_speakers'] = len(speakers)
            
            # Default speaker genders
            session['speaker_genders'] = ['M'] * len(speakers)
            
            # Save diarization data to files
            output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id)
            save_diarization_data(output_dir, transcript, segments)
            
            return jsonify({
                'success': True,
                'language': display_language,
                'transcription': transcript,
                'diarization': {
                    'segments': segments
                }
            })
            
        except Exception as e:
            error_message = str(e)
            print(f"Exception in detect_language: {error_message}")
            return jsonify({'error': error_message}), 500
        
    except Exception as e:
        import traceback
        print(f"Error in detect_language: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Return transcription from session (already processed during language detection)."""
    try:
        # Get session_id from request
        try:
            # First try to get data from JSON
            request_data = request.get_json() or {}
        except:
            # If that fails, it's not JSON data
            request_data = {}
            
        # Get data from form if available
        form_data = request.form
        
        # Get session_id, prioritizing form data
        session_id = form_data.get('session_id') or request_data.get('session_id')
        
        # Get target_language directly from request data, using the same pattern as translation endpoint
        
        print(f"Received target_language from metadata: {get_metadata_field(session_id, 'target_language', None)}")
        print(f"Received target_language from request data: {request_data.get('target_language')}")
        print(f"Received target_language from form data: {form_data.get('target_language')}")
        print(f"Received target_language from session: {session.get('target_language')}")
        target_language = request_data.get('target_language') or form_data.get('target_language', 'english')
        session['target_language'] = target_language
        print(f"Updated target_language in session from request data: {target_language}")
        
        # Handle preserve_background_music in the same robust way as the translation endpoint
        # First read the existing value from metadata
        existing_preserve_background_music = get_metadata_field(session_id, "preserve_background_music", None)
        print(f"Retrieved preserve_background_music from metadata: {existing_preserve_background_music!r}")
        
        # Get background music preference from form data
        preserve_background_music_str = form_data.get('preserve_background_music')
        print(f"Raw form data for preserve_background_music: {preserve_background_music_str!r}")
        
        # If not in form data, try JSON data
        if preserve_background_music_str is None:
            # Try JSON data
            raw_json_value = request_data.get('preserve_background_music')
            if raw_json_value is not None:
                preserve_background_music_str = raw_json_value
                print(f"Raw JSON data for preserve_background_music: {preserve_background_music_str!r}")
            # If neither form nor JSON has a value, use the existing value from metadata
            elif existing_preserve_background_music is not None:
                print(f"Using existing value from metadata: {existing_preserve_background_music}")
                preserve_background_music = existing_preserve_background_music
                # Skip the conversion logic below
                preserve_background_music_str = None
            else:
                # Only use default if we have no existing value
                preserve_background_music_str = 'false'
                print(f"No value found, using default: {preserve_background_music_str!r}")
        
        # Convert string to boolean
        if preserve_background_music_str is not None:
            if isinstance(preserve_background_music_str, str):
                # Handle multiple possible string values
                preserve_background_music_str = preserve_background_music_str.lower().strip()
                if preserve_background_music_str in ('true', 'yes', '1', 'on'):
                    preserve_background_music = True
                else:
                    preserve_background_music = False
                print(f"String value '{preserve_background_music_str}' converted to boolean: {preserve_background_music}")
            else:
                # Handle case where it might be a boolean already
                preserve_background_music = bool(preserve_background_music_str)
                print(f"Non-string value {preserve_background_music_str!r} converted to boolean: {preserve_background_music}")
        
        print(f"Final preserve_background_music value: {preserve_background_music}")
        
        # Store in session for later use
        session['preserve_background_music'] = preserve_background_music
        print(f"Value stored in session: {session.get('preserve_background_music')}")
        
        # Directly update the preserve_background_music field in metadata
        update_metadata_field(session_id, "preserve_background_music", preserve_background_music)
        print(f"Re-saved preserve_background_music to metadata: {preserve_background_music}")
        
        print(f"Received session_id: {session_id}")
        
        # Get transcription from session
        transcription = session.get('transcription')
        if not transcription:
            # If not in session, check if we need to process the audio
            upload_path = session.get('upload_path')
            if not upload_path:
                # Look for the file based on session_id
                potential_file_paths = [
                    get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.wav"),
                    get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.mp3"),
                    get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.webm"),
                    get_upload_path(app.config['UPLOAD_FOLDER'], f"{session_id}.ogg")
                ]
                
                for path in potential_file_paths:
                    if os.path.exists(path):
                        upload_path = path
                        break
                        
            if not upload_path:
                return jsonify({'error': 'No audio file found for this session'}), 400
            
            # Double-check that the file actually exists
            if not os.path.exists(upload_path):
                print(f"Error: File path exists in session but file not found: {upload_path}")
                
                # Try to find an alternative file with the same session ID but different extension
                base_path = os.path.splitext(upload_path)[0]
                for ext in ['.wav', '.mp3', '.webm', '.ogg']:
                    alt_path = f"{base_path}{ext}"
                    if os.path.exists(alt_path):
                        print(f"Found alternative file: {alt_path}")
                        upload_path = alt_path
                        session['upload_path'] = upload_path
                        break
                
                # If still no file found, return error
                if not os.path.exists(upload_path):
                    return jsonify({'error': 'Audio file not found on server'}), 400
                    
            print(f"Found audio file at: {upload_path} (Size: {os.path.getsize(upload_path)} bytes)")
            
            # Check if API key is available
            if not SARVAM_API_KEY:
                print("Error: SARVAM_API_KEY not found in environment variables")
                return jsonify({'error': 'Speech recognition service is not configured properly'}), 500
            
            # Create output directory for VAD segments
            vad_output_dir = os.path.join(app.config['OUTPUT_FOLDER'], session_id, "vad_segments")
            ensure_dir(vad_output_dir)
            
            # Get VAD and diarization configurations
            vad_config = get_vad_config()
            
            print(f"Using VAD with threshold: {vad_config['threshold']}, combine_duration: {vad_config['combine_duration']}s")
            
            # Use asyncio to run the async transcribe_with_vad_diarization function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Use the new VAD-enhanced diarization function with proper parameters
                result = loop.run_until_complete(
                    transcribe_with_vad_diarization(
                        audio_path=upload_path,
                        vad_segments_dir=vad_output_dir,
                        min_segment_duration=vad_config.get('min_segment_duration', 1.0)
                    )
                )
                loop.close()
                
                # Check for errors in the result
                if 'error' in result:
                    error_message = result.get('error', 'Failed to process audio')
                    print(f"Error in transcribe_with_vad_diarization: {error_message}")
                    
                    # If we have previous transcription results in the session, use those
                    if 'transcription' in session:
                        print(f"Using existing transcription from session: {session['transcription'][:50]}...")
                        return jsonify({
                            'success': True,
                            'message': 'Using existing transcription due to API error',
                            'language': session.get('source_language', 'unknown'),
                            'transcription': session.get('transcription', ''),
                            'diarization': session.get('diarization', {'segments': [], 'speakers': {}})
                        })
                    
                    return jsonify({'error': error_message}), 500
                
                # Process successful result
                language_code = result.get('language_code', 'hi-IN')  # Default to Hindi if not detected
                transcript = result.get('transcript', '')
                segments = result.get('segments', [])
                
                # Verify we have actual segments before proceeding
                if not segments:
                    print(f"Warning: No segments found in transcription result. This may indicate an audio processing issue.")
                    return jsonify({'error': 'No speech segments detected in the audio. Please check the audio file.'}), 400
                
                # Map language codes to display names
                language_map = {
                    'hi-IN': 'hindi',
                    'te-IN': 'telugu',
                    'ta-IN': 'tamil',
                    'kn-IN': 'kannada',
                    'ml-IN': 'malayalam',
                    'bn-IN': 'bengali',
                    'en-IN': 'english'
                }
                
                display_language = language_map.get(language_code, language_code)
                
                # Process speakers with detailed attributes
                speakers = {}
                for i, segment in enumerate(segments):
                    speaker_id = segment.get('speaker', f'SPEAKER_{i}')
                    if speaker_id not in speakers:
                        speakers[speaker_id] = {
                            'id': speaker_id,
                            'gender': 'M',  # Default gender
                            'segments': []
                        }
                    
                    # Propagate gender to segment
                    segment['gender'] = speakers[speaker_id]['gender']
                    
                    speakers[speaker_id]['segments'].append({
                        'start': segment.get('start', 0),
                        'end': segment.get('end', 0),
                        'text': segment.get('text', '')
                    })
                
                # Store results in session
                session['upload_path'] = upload_path
                session['source_language'] = language_code
                session['target_language'] = display_language
                session['transcription'] = transcript
                session['session_id'] = session_id
                session['diarization'] = {
                    'segments': segments,
                    'speakers': speakers
                }
                session['num_speakers'] = len(speakers)
                session['speaker_genders'] = ['M'] * len(speakers)
                
                transcription = transcript
                
            except Exception as e:
                error_message = str(e)
                print(f"Exception in transcribe: {error_message}")
                return jsonify({'error': error_message}), 500
        
        # Get diarization data
        diarization = session.get('diarization', {})
        segments = diarization.get('segments', [])
        speakers = diarization.get('speakers', {})
        
        # Get language information
        source_language = session.get('source_language', '')
        target_language = request_data.get('target_language') or form_data.get('target_language', 'english')
        
        # Save diarization data to files (this was previously only done in detect_language)
        output_dir = os.path.join("outputs", session_id)
        diarization_file = os.path.join(output_dir, "diarization.json")

        # If the file exists, read the segments from it instead of using session data
        if os.path.exists(diarization_file):
            try:
                print(f"Reading existing diarization file to preserve edits: {diarization_file}")
                with open(diarization_file, 'r') as f:
                    diarization_data = json.load(f)
                    # Use the segments from the file (which include any edits)
                    edited_segments = diarization_data.get('segments', segments)
                    print(f"Using {len(edited_segments)} segments from edited diarization file")
                    # Save with the edited segments
                    save_diarization_data(output_dir, transcription, edited_segments)
            except Exception as e:
                print(f"Error reading diarization file: {str(e)}")
                # Fallback to session data if file can't be read
                print(f"Falling back to session data with {len(segments)} segments")
                save_diarization_data(output_dir, transcription, segments)
        else:
            # If file doesn't exist, use session data
            print(f"No existing diarization file found, using session data with {len(segments)} segments")
            save_diarization_data(output_dir, transcription, segments)
        
        # Save metadata
        metadata = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "source_language": source_language,
            "target_language": target_language,  # Use the value directly from request
            "preserve_background_music": get_metadata_field(session_id, "preserve_background_music", False),  # Use the properly handled value
            "transcription_completed_at": datetime.now().isoformat()
        }
        
        # Use the metadata manager to update metadata instead of overwriting the file
        update_metadata(session_id, metadata)
        print(f"Updated metadata with transcription information using append-only approach")
        
        # Store in session for future use
        session['source_language'] = source_language
        session['target_language'] = target_language
        session['preserve_background_music'] = get_metadata_field(session_id, "preserve_background_music", False)
        
        return jsonify({
            'success': True,
            'transcription': transcription,
            'segments': segments,
            'speakers': speakers,
            'language': source_language,
            'language_name': target_language
        })
        
    except Exception as e:
        import traceback
        print(f"Error in transcribe: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def translate():
    """
    Translate transcription to target language.
    """
    try:
        # Add detailed logging
        print("==== TRANSLATION DEBUG ==== Starting /api/translate endpoint")
        
        # Get request data
        request_data = request.get_json() or {}
        form_data = request.form
        
        print(f"Request JSON: {request_data}")
        print(f"Request Form: {form_data}")
        
        # Get session ID and target language
        session_id = request_data.get('session_id') or form_data.get('session_id')
        target_language = request_data.get('target_language') or form_data.get('target_language', 'english')
        
        print(f"==== TRANSLATION DEBUG ==== Session ID: {session_id}, Target Language: {target_language}")
        
        # Store target_language in session
        session['target_language'] = target_language
        
        # Update metadata.json with the target_language from form data
        update_metadata_field(session_id, "target_language", target_language)
        print(f"==== TRANSLATION DEBUG ==== Updated target_language in metadata: {target_language}")
        
        if not session_id:
            print("==== TRANSLATION DEBUG ==== Error: No session ID provided")
            return jsonify({"error": "Session ID is required"}), 400
        
        # Check if diarization.json exists
        diarization_file = os.path.join("outputs", session_id, "diarization.json")
        print(f"==== TRANSLATION DEBUG ==== Checking for diarization file at: {diarization_file}")
        print(f"==== TRANSLATION DEBUG ==== File exists: {os.path.exists(diarization_file)}")
        
        # CRITICAL FIX: First read the existing value from metadata
        existing_preserve_background_music = get_metadata_field(session_id, "preserve_background_music", None)
        print(f"==== TRANSLATION DEBUG ==== Existing preserve_background_music from metadata: {existing_preserve_background_music!r}")
        
        # Get background music preference with enhanced logging and handling
        preserve_background_music_str = form_data.get('preserve_background_music')
        print(f"==== TRANSLATION DEBUG ==== Raw form data for preserve_background_music: {preserve_background_music_str!r}")
        
        # If not in form data, try JSON data
        if preserve_background_music_str is None:
            # Only use JSON data if it's explicitly provided (not the default 'false')
            raw_json_value = request_data.get('preserve_background_music')
            if raw_json_value is not None:
                preserve_background_music_str = raw_json_value
                print(f"==== TRANSLATION DEBUG ==== Raw JSON data for preserve_background_music: {preserve_background_music_str!r}")
            # If neither form nor JSON has a value, use the existing value from metadata
            elif existing_preserve_background_music is not None:
                print(f"==== TRANSLATION DEBUG ==== Using existing value from metadata: {existing_preserve_background_music}")
                preserve_background_music = existing_preserve_background_music
                # Skip the conversion logic below
                preserve_background_music_str = None
            else:
                # Only use default if we have no existing value
                preserve_background_music_str = 'false'
                print(f"==== TRANSLATION DEBUG ==== No value found, using default: {preserve_background_music_str!r}")
        
        # Convert string to boolean with detailed logging
        if preserve_background_music_str is not None:
            if isinstance(preserve_background_music_str, str):
                # Handle multiple possible string values
                preserve_background_music_str = preserve_background_music_str.lower().strip()
                if preserve_background_music_str in ('true', 'yes', '1', 'on'):
                    preserve_background_music = True
                else:
                    preserve_background_music = False
                print(f"==== TRANSLATION DEBUG ==== String value '{preserve_background_music_str}' converted to boolean: {preserve_background_music}")
            else:
                # Handle case where it might be a boolean already
                preserve_background_music = bool(preserve_background_music_str)
                print(f"==== TRANSLATION DEBUG ==== Non-string value {preserve_background_music_str!r} converted to boolean: {preserve_background_music}")
        
        print(f"==== TRANSLATION DEBUG ==== Final preserve_background_music value: {preserve_background_music}")
        
        # Store in session for later use
        session['preserve_background_music'] = preserve_background_music
        print(f"==== TRANSLATION DEBUG ==== Value stored in session: {session.get('preserve_background_music')}")
        
        # CRITICAL FIX: Directly update the preserve_background_music field in metadata
        # This ensures it's set correctly regardless of other metadata operations
        update_metadata_field(session_id, "preserve_background_music", preserve_background_music)
        print(f"==== TRANSLATION DEBUG ==== Value directly updated in metadata: {preserve_background_music}")
        
        # Translate diarization data
        try:
            print("==== TRANSLATION DEBUG ==== About to call translate_and_save_diarization")
            results = translate_and_save_diarization(session_id, target_language)
            print(f"==== TRANSLATION DEBUG ==== translate_and_save_diarization returned: {results.get('success', False)}")
            
            # Check if translation was successful
            if not results.get("success", False):
                error_message = results.get("error", "Unknown error in diarization translation")
                print(f"==== TRANSLATION DEBUG ==== Error in diarization translation: {error_message}")
                
                # If we have previous transcription results in the session, use those
                if 'transcription' in session:
                    print(f"==== TRANSLATION DEBUG ==== Using existing transcription from session: {session['transcription'][:50]}...")
                    return jsonify({
                        'success': True,
                        'message': 'Using existing transcription due to API error',
                        'language': session.get('source_language', 'unknown'),
                        'transcription': session.get('transcription', ''),
                        'diarization': session.get('diarization', {'segments': [], 'speakers': {}})
                    })
                
                return jsonify({'error': error_message}), 500
            
            # Process successful result
            print("==== TRANSLATION DEBUG ==== Translation completed successfully")
            
            # CRITICAL FIX: Re-save the preserve_background_music preference to ensure it's not lost
            # This ensures the preference is preserved after translation
            update_metadata_field(session_id, "preserve_background_music", preserve_background_music)
            print(f"==== TRANSLATION DEBUG ==== Re-saved preserve_background_music to metadata: {preserve_background_music}")
            
            return jsonify({
                "success": True,
                "message": "Translation completed with diarization",
                "diarization_paths": results.get("diarization_paths", {}),
                "translation_paths": results.get("translation_paths", {}),
                "translation": results.get("full_translation", "")
            })
            
        except FileNotFoundError as e:
            print(f"==== TRANSLATION DEBUG ==== FileNotFoundError: {str(e)}")
            
            # Fall back to traditional translation
            print("==== TRANSLATION DEBUG ==== Falling back to traditional translation")
            
            # Get transcription file path
            transcription_file = os.path.join("outputs", session_id, "transcription", f"{session_id}.txt")
            print(f"==== TRANSLATION DEBUG ==== Checking for transcription file at: {transcription_file}")
            print(f"==== TRANSLATION DEBUG ==== File exists: {os.path.exists(transcription_file)}")
            
            if not os.path.exists(transcription_file):
                return jsonify({"error": "Transcription file not found"}), 404
            
            # Read transcription
            with open(transcription_file, 'r', encoding='utf-8') as f:
                transcription = f.read()
            
            # Get source language from metadata
            metadata_path = os.path.join("outputs", session_id, "metadata.json")
            source_language = "english"  # Default
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    source_language = metadata.get("source_language", "english")
            
            # Translate using traditional method
            print(f"==== TRANSLATION DEBUG ==== Using traditional translation method with source_language={source_language}, target_language={target_language}")
            from modules.google_translation import translate_text
            translated_text = translate_text(transcription, source_language, target_language)
            
            # Save translation
            translation_dir = os.path.join("outputs", session_id, "translation")
            os.makedirs(translation_dir, exist_ok=True)
            translation_path = os.path.join(translation_dir, f"{target_language}.txt")
            
            with open(translation_path, 'w', encoding='utf-8') as f:
                f.write(translated_text)
            
            print(f"==== TRANSLATION DEBUG ==== Translation saved to: {translation_path}")
            
            return jsonify({
                "success": True,
                "message": "Translation completed with fallback method",
                "translation_path": translation_path,
                "translation": translated_text
            })
            
    except Exception as e:
        print(f"==== TRANSLATION DEBUG ==== Unhandled exception: {str(e)}")
        print(f"==== TRANSLATION DEBUG ==== Exception type: {type(e).__name__}")
        import traceback
        print(f"==== TRANSLATION DEBUG ==== Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/synthesize', methods=['POST'])
def synthesize():
    """
    Synthesize speech from translated text using time-aligned approach.
    This endpoint now redirects to the time-aligned synthesis for consistent behavior.
    """
    # Log deprecation warning
    print("WARNING: /api/synthesize endpoint is deprecated. Using time-aligned synthesis instead.")
    
    # Redirect to time-aligned synthesis
    return synthesize_time_aligned()

@app.route('/api/synthesize-time-aligned', methods=['POST'])
def synthesize_time_aligned():
    """Synthesize speech with time alignment to original audio."""
    try:
        # Get session_id from request
        session_id = request.json.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
            
        # Get target language from request
        target_language = request.json.get('target_language')
        if not target_language:
            return jsonify({'error': 'No target language specified'}), 400
        
        # CRITICAL FIX: First read the existing value from metadata
        existing_preserve_background_music = get_metadata_field(session_id, "preserve_background_music", None)
        print(f"==== TTS DEBUG ==== Existing preserve_background_music from metadata: {existing_preserve_background_music!r}")
        
        # Get background music preference with enhanced logging and handling
        preserve_background_music_str = request.json.get('preserve_background_music')
        print(f"==== TTS DEBUG ==== Raw JSON data for preserve_background_music: {preserve_background_music_str!r}")
        
        # If not in JSON data, use the existing value from metadata
        if preserve_background_music_str is None:
            if existing_preserve_background_music is not None:
                print(f"==== TTS DEBUG ==== Using existing value from metadata: {existing_preserve_background_music}")
                preserve_background_music = existing_preserve_background_music
                # Skip the conversion logic below
                preserve_background_music_str = None
            else:
                # Only use default if we have no existing value
                preserve_background_music_str = 'false'
                print(f"==== TTS DEBUG ==== No value found, using default: {preserve_background_music_str!r}")
        
        # Convert string to boolean with detailed logging
        if preserve_background_music_str is not None:
            if isinstance(preserve_background_music_str, str):
                # Handle multiple possible string values
                preserve_background_music_str = preserve_background_music_str.lower().strip()
                if preserve_background_music_str in ('true', 'yes', '1', 'on'):
                    preserve_background_music = True
                else:
                    preserve_background_music = False
                print(f"==== TTS DEBUG ==== String value '{preserve_background_music_str}' converted to boolean: {preserve_background_music}")
            else:
                # Handle case where it might be a boolean already
                preserve_background_music = bool(preserve_background_music_str)
                print(f"==== TTS DEBUG ==== Non-string value {preserve_background_music_str!r} converted to boolean: {preserve_background_music}")
        
        print(f"==== TTS DEBUG ==== Final preserve_background_music value: {preserve_background_music}")
        
        # Store in session for later use
        session['preserve_background_music'] = preserve_background_music
        print(f"==== TTS DEBUG ==== Value stored in session: {session.get('preserve_background_music')}")
        
        # Re-save it to metadata to ensure it's not lost
        update_metadata_field(session_id, "preserve_background_music", preserve_background_music)
        print(f"==== TTS DEBUG ==== Re-saved preserve_background_music to metadata: {preserve_background_music}")
        
        # Get speaker details from request
        speaker_details = request.json.get('speaker_details', [])
        
        # Determine provider based on target language - always use Cartesia for Hindi, Sarvam for others
        provider = 'cartesia' if target_language.lower() == 'hindi' else 'sarvam'
        
        # Get TTS options
        options = {}
        
        # For Sarvam
        if provider == 'sarvam':
            options['pitch'] = float(request.json.get('pitch', 0))
            options['pace'] = float(request.json.get('pace', 1.0))
            options['loudness'] = float(request.json.get('loudness', 1.0))
        
        # For Cartesia
        if provider == 'cartesia':
            options['bit_rate'] = int(request.json.get('bit_rate', 128000))
            options['sample_rate'] = int(request.json.get('sample_rate', 44100))
        
        # Check if diarization exists
        diarization_file = os.path.join("outputs", session_id, "diarization.json")
        if not os.path.exists(diarization_file):
            return jsonify({'error': 'Diarization file not found'}), 404
        
        # Check if translation exists
        translation_file = os.path.join("outputs", session_id, "diarization_translated.json")
        if not os.path.exists(translation_file):
            return jsonify({'error': 'Translation file not found'}), 404
        
        # Generate output filename
        output_filename = f"{session_id}_time_aligned.{'mp3' if provider == 'cartesia' else 'wav'}"
        output_path = get_output_path(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Create TTS processor
        from modules.tts_processor import TTSProcessor
        
        # Create a mapping of speaker_id to voice_id
        speaker_voice_map = {}
        for speaker in speaker_details:
            if speaker.get('speaker_id') and speaker.get('voice_id'):
                # Convert from "speaker_1" format to "SPEAKER_XX" format
                speaker_num = speaker.get('speaker_id').split('_')[1]
                # Format as SPEAKER_XX (e.g., "1" -> "SPEAKER_00")
                diarization_speaker_id = f"SPEAKER_{int(speaker_num)-1:02d}"
                speaker_voice_map[diarization_speaker_id] = speaker.get('voice_id')
                print(f"Mapped UI speaker {speaker.get('speaker_id')} to diarization speaker {diarization_speaker_id} with voice {speaker.get('voice_id')}")
        
        # Log the complete mapping for debugging
        print(f"Speaker-voice mapping: {speaker_voice_map}")
        
        # Create TTS processor with speaker details
        tts_processor = TTSProcessor(
            output_dir=os.path.join("outputs", session_id),
            provider=provider,
            language=target_language,
            options=options,
            speaker_voice_map=speaker_voice_map  # Pass the speaker-voice mapping
        )
        
        # Process TTS with time alignment
        try:
            output_file = tts_processor.process_tts_with_time_alignment(
                diarization_file=translation_file
            )
            
            if not output_file or not os.path.exists(output_file):
                return jsonify({'error': 'Failed to generate time-aligned audio'}), 500
                
            # Save synthesized audio to session directory
            with open(output_file, 'rb') as f:
                audio_data = f.read()
            
            # Save audio data
            audio_format = 'mp3' if provider == 'cartesia' else 'wav'
            saved_path = save_synthesized_audio(session_id, audio_data, target_language, format=audio_format)
            
            # Update TTS metadata fields individually to ensure no overwriting
            update_metadata_field(session_id, "tts_completed_at", datetime.now().isoformat())
            update_metadata_field(session_id, "provider", provider)
            update_metadata_field(session_id, "audio_format", audio_format)
            update_metadata_field(session_id, "time_aligned", True)
            update_metadata_field(session_id, "synthesized_audio_path", saved_path)
            
            # Update speaker details as a section
            update_metadata_section(session_id, "speaker_details", {"speakers": speaker_details})
            
            # Update TTS options as a section
            update_metadata_section(session_id, "options", options)
            
            # No need to explicitly preserve background_music preference as it will be preserved
            # by our append-only metadata manager
            
            # Get the updated metadata for logging
            updated_metadata = get_metadata(session_id)
            print(f"Updated metadata: {updated_metadata}")
            
            # Get URL for the audio file (serve from /outputs/session_id/tts/)
            audio_url = f"/outputs/{session_id}/tts/final_output_{target_language.lower()}_{session_id}.{audio_format}"
            
            return jsonify({
                'success': True,
                'audio_url': audio_url
            })
            
        except Exception as e:
            print(f"Error in TTS processing: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return jsonify({'error': f'TTS processing error: {str(e)}'}), 500
    except Exception as e:
        import traceback
        print(f"Error in synthesize_time_aligned: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate translation quality using advanced metrics including BERT and BLEU scores."""
    try:
        # Get session_id from request
        session_id = request.json.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
            
        # Check if required files exist
        base_dir = 'outputs'
        diarization_path = os.path.join(base_dir, session_id, 'diarization.json')
        translation_path = os.path.join(base_dir, session_id, 'diarization_translated.json')
        
        if not os.path.exists(diarization_path):
            return jsonify({'error': 'Diarization file not found'}), 404
            
        if not os.path.exists(translation_path):
            return jsonify({'error': 'Translation file not found'}), 404
        
        # Perform advanced validation with BERT and BLEU scores
        validation_result = validate_translation_with_metrics(session_id, base_dir)
        
        if 'error' in validation_result:
            return jsonify({'error': validation_result['error']}), 500
        
        # For backward compatibility with UI, use BERT score as the similarity_score
        bert_score = validation_result.get('metrics', {}).get('bert_overall', 0.0)
        
        # Update metadata with validation results
        update_metadata_section(
            session_id=session_id,
            section_name='validation',
            section_data={
                'advanced_metrics': True,
                'bert_overall': validation_result.get('metrics', {}).get('bert_overall', 0),
                'bleu_overall': validation_result.get('metrics', {}).get('bleu_overall', 0),
                'enhanced_composite_score': validation_result.get('enhanced_composite_score', 0),
                'audio_extraction_score': validation_result.get('audio_extraction_score', 0),
                'bert_segment_weighted': validation_result.get('metrics', {}).get('bert_segment_weighted', 0),
                'bleu_segment_weighted': validation_result.get('metrics', {}).get('bleu_segment_weighted', 0)
            }
        )
        
        return jsonify({
            'success': True,
            'similarity_score': bert_score,  # Use BERT score for UI compatibility
            'validation_result': validation_result
        })
        
    except Exception as e:
        import traceback
        print(f"Error in validate: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate_advanced', methods=['POST'])
def validate_advanced():
    """
    Validate translation quality using advanced metrics including BERT and BLEU scores.
    This endpoint performs back-translation and calculates BERT and BLEU scores
    for both the overall translation and segment-wise.
    """
    try:
        # Get session_id from request
        session_id = request.json.get('session_id')
        if not session_id:
            return jsonify({'error': 'No session ID provided'}), 400
        
        # Check if required files exist
        base_dir = 'outputs'
        diarization_path = os.path.join(base_dir, session_id, 'diarization.json')
        translation_path = os.path.join(base_dir, session_id, 'diarization_translated.json')
        
        if not os.path.exists(diarization_path):
            return jsonify({'error': 'Diarization file not found'}), 404
            
        if not os.path.exists(translation_path):
            return jsonify({'error': 'Translation file not found'}), 404
        
        # Perform advanced validation with BERT and BLEU scores
        validation_result = validate_translation_with_metrics(session_id, base_dir)
        
        if 'error' in validation_result:
            return jsonify({'error': validation_result['error']}), 500
        
        # Update metadata with validation results
        update_metadata_section(
            session_id=session_id,
            section_name='validation',
            section_data={
                'advanced_metrics': True,
                'bert_overall': validation_result.get('metrics', {}).get('bert_overall', 0),
                'bleu_overall': validation_result.get('metrics', {}).get('bleu_overall', 0),
                'enhanced_composite_score': validation_result.get('enhanced_composite_score', 0),
                'audio_extraction_score': validation_result.get('audio_extraction_score', 0),
                'bert_segment_weighted': validation_result.get('metrics', {}).get('bert_segment_weighted', 0),
                'bleu_segment_weighted': validation_result.get('metrics', {}).get('bleu_segment_weighted', 0)
            }
        )
        
        return jsonify({
            'success': True,
            'validation_result': validation_result
        })
        
    except Exception as e:
        import traceback
        print(f"Error in advanced validation: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_voices', methods=['GET'])
def get_voices():
    """Get available voices for TTS based on language."""
    try:
        # Get target language from query params
        language = request.args.get('language')
        
        # Get available voices
        voices = get_available_voices(language)
        
        return jsonify({
            'success': True,
            'voices': voices
        })
        
    except Exception as e:
        import traceback
        print(f"Error in get_voices: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-voices-by-language', methods=['GET'])
def get_voices_by_language():
    """Get available voices for a specific language."""
    try:
        # Get language from request
        language = request.args.get('language', 'english').lower()
        
        # Determine which TTS provider to use based on language
        if language == 'hindi':
            # For Hindi, use Cartesia voices
            from modules.cartesia_tts import get_available_voices
            voices = get_available_voices()
        else:
            # For other languages, use Sarvam voices
            from modules.sarvam_tts import get_available_voices
            voices = get_available_voices(language)
        
        return jsonify({
            'success': True,
            'voices': voices
        })
    
    except Exception as e:
        print(f"Error getting voices: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/api_save_diarization', methods=['POST'])
def api_save_diarization():
    """Save edited diarization data."""
    try:
        print("=== DIARIZATION SAVE DEBUG START ===")
        session_id = request.json['session_id']
        updates = request.json['updates']
        
        print(f"Received diarization updates for session: {session_id}")
        print(f"Updates payload: {json.dumps(updates, indent=2, ensure_ascii=False)}")
        
        # Validate session dir exists
        session_dir = os.path.join('outputs', session_id)
        if not os.path.isdir(session_dir):
            print(f"Invalid session directory: {session_dir}")
            return jsonify({'success': False, 'error': 'Invalid session'})
            
        # Load and update only allowed fields
        diarization_file = os.path.join(session_dir, 'diarization.json')
        print(f"Loading diarization file: {diarization_file}")
        with open(diarization_file) as f:
            data = json.load(f)
            
        # Log original data structure
        print(f"Original segments count: {len(data['segments'])}")
        
        update_count = 0
        text_update_count = 0
        speaker_update_count = 0
        
        for seg_id, changes in updates.items():
            for segment in data['segments']:
                if str(segment['segment_id']) == str(seg_id):
                    print(f"Processing segment {seg_id}:")
                    
                    if 'speaker' in changes:
                        old_speaker = segment.get('speaker', 'None')
                        segment['speaker'] = str(changes['speaker'])
                        print(f"  Updated speaker: {old_speaker} -> {segment['speaker']}")
                        speaker_update_count += 1
                        
                    if 'text' in changes:
                        old_text = segment.get('text', '')
                        segment['text'] = str(changes['text'])
                        print(f"  Updated text: '{old_text}' -> '{segment['text']}'")
                        text_update_count += 1
                        
                    update_count += 1
        
        print(f"Updated {update_count} segments total ({speaker_update_count} speaker updates, {text_update_count} text updates)")
        
        # Update the transcript field to reflect edited text
        full_transcript = ' '.join([segment['text'] for segment in data['segments']])
        data['transcript'] = full_transcript
        print(f"Updated full transcript (length: {len(full_transcript)})")
        
        # Atomic write
        temp_path = os.path.join(session_dir, 'diarization.tmp')
        final_path = os.path.join(session_dir, 'diarization.json')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, final_path)
        print(f"Saved updated diarization data to {final_path}")
        
        # CRITICAL FIX: Preserve the existing preserve_background_music value
        # Read the current value from metadata
        existing_preserve_background_music = get_metadata_field(session_id, "preserve_background_music", None)
        print(f"Existing preserve_background_music from metadata: {existing_preserve_background_music!r}")
        
        # If a value exists, ensure it's preserved in the session for subsequent calls
        if existing_preserve_background_music is not None:
            session['preserve_background_music'] = existing_preserve_background_music
            print(f"Preserved existing value in session: {existing_preserve_background_music}")
        
        # CRITICAL FIX: Preserve the existing target_language value
        # Read the current value from metadata
        existing_target_language = get_metadata_field(session_id, "target_language", None)
        print(f"Existing target_language from metadata: {existing_target_language!r}")
        
        # If a value exists, ensure it's preserved in the session for subsequent calls
        if existing_target_language is not None:
            session['target_language'] = existing_target_language
            print(f"Preserved target_language in session: {existing_target_language}")
        
        print("=== DIARIZATION SAVE DEBUG END ===")
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving diarization: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get_diarization', methods=['GET'])
def get_diarization():
    """Get diarization data for editing."""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            print("Error: Session ID is required")
            return jsonify({'error': 'Session ID is required'}), 400
            
        # Load diarization data
        diarization_path = os.path.join('outputs', session_id, 'diarization.json')
        if not os.path.exists(diarization_path):
            print(f"Error: Diarization data not found at {diarization_path}")
            return jsonify({'error': 'Diarization data not found'}), 404
            
        print(f"Loading diarization data from {diarization_path}")
        with open(diarization_path) as f:
            data = json.load(f)
            
        print(f"Diarization data loaded successfully with {len(data.get('segments', []))} segments")
        return jsonify(data)
    except Exception as e:
        print(f"Error getting diarization: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcription/<session_id>')
def show_transcription(session_id):
    """Display transcription results."""
    # Verify session exists
    session_dir = os.path.join('outputs', session_id)
    if not os.path.isdir(session_dir):
        return "Invalid session", 404
        
    return render_template(
        'transcription.html',
        session_id=session_id
    )

@app.route('/editor/<session_id>')
def diarization_editor(session_id):
    """Serve the diarization editor interface."""
    # Verify session exists
    session_dir = os.path.join('outputs', session_id)
    if not os.path.isdir(session_dir):
        return "Invalid session", 404
        
    # Load diarization data
    diarization_path = os.path.join(session_dir, 'diarization.json')
    with open(diarization_path) as f:
        diarization_data = json.load(f)
    
    return render_template(
        'diarization_editor.html',
        session_id=session_id,
        segments=diarization_data['segments'],
        speakers=list({seg['speaker'] for seg in diarization_data['segments']})
    )

@app.route('/outputs/<filename>')
def output_file(filename):
    """Serve output files."""
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/uploads/<filename>')
def upload_file_route(filename):
    """Serve uploaded files."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/outputs/<session_id>/synthesis/<filename>')
def serve_synthesis(session_id, filename):
    """Serve synthesized audio files."""
    synthesis_dir = os.path.join("outputs", session_id, "synthesis")
    return send_from_directory(synthesis_dir, filename)

@app.route('/outputs/<session_id>/tts/<filename>')
def serve_tts(session_id, filename):
    """Serve synthesized TTS audio files."""
    tts_dir = os.path.join('outputs', session_id, 'tts')
    return send_from_directory(tts_dir, filename)

# --- Serve outputs directory statically for audio validation ---
from flask import send_from_directory
@app.route('/outputs/<path:filename>')
def serve_outputs(filename):
    outputs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'outputs'))
    return send_from_directory(outputs_dir, filename)
# --- End static outputs serving ---

@app.route('/test-diarization-editor')
def test_diarization_editor():
    """Test route for diarization editor with sample data."""
    # Load sample diarization data
    sample_path = 'temp/diarization.json'
    
    try:
        # If the sample file doesn't exist, create it with test data
        if not os.path.exists(sample_path):
            os.makedirs(os.path.dirname(sample_path), exist_ok=True)
            test_data = {
                "transcript": "हेलो मैं यूलू से अर्पिता बात कर रही हूँ। मैंने देखा कि आपने रेंटल प्लान नहीं खरीदा।",
                "segments": [
                    {
                        "segment_id": "seg_000",
                        "speaker": "SPEAKER_00",
                        "text": "हेलो मैं यूलू से अर्पिता बात कर रही हूँ।",
                        "start_time": 0.522,
                        "end_time": 3.512,
                        "gender": "unknown",
                        "pace": 1.0
                    },
                    {
                        "segment_id": "seg_001",
                        "speaker": "SPEAKER_01",
                        "text": "मैंने देखा कि आपने रेंटल प्लान नहीं खरीदा।",
                        "start_time": 3.826,
                        "end_time": 6.725,
                        "gender": "unknown",
                        "pace": 1.0
                    }
                ],
                "language_code": "hi-IN"
            }
            with open(sample_path, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2)
        
        # Load the sample data
        with open(sample_path, encoding='utf-8') as f:
            data = json.load(f)
            
        # Render template with sample data
        return render_template(
            'test_diarization_editor.html',
            sample_data=json.dumps(data)
        )
    except Exception as e:
        return f"Error loading test data: {str(e)}", 500

@app.route('/api/transliterate', methods=['POST'])
def transliterate():
    """
    Transliterate text from Roman script to the specified language script.
    Uses Google Input Tools API for transliteration.
    """
    data = request.json
    text = data.get('text', '')
    language = data.get('language', 'en')

    def is_roman(word):
        # Returns True if the word is in basic Latin script (A-Z, a-z, 0-9, basic punctuation)
        return all((('A' <= c <= 'Z') or ('a' <= c <= 'z') or ('0' <= c <= '9') or c in "'-.,?!") for c in word)

    SPECIAL_CHARS = {' ', '.', ',', '|', '!'}

    # Map language to Google's transliteration format
    google_language_code = get_google_transliteration_code(language)

    app.logger.info(f"Transliteration request - Text: '{text}', Language: {language}, Google Code: {google_language_code}")

    try:
        words = text.split(' ')
        transliterated_words = []
        for word in words:
            # If the word is a special character or empty, append as is
            if word in SPECIAL_CHARS or word == '':
                transliterated_words.append(word)
            elif is_roman(word):
                url = f"https://inputtools.google.com/request?text={word}&itc={google_language_code}&num=5&cp=0&cs=1&ie=utf-8&oe=utf-8"
                response = requests.get(url)
                response_data = response.json()
                if response_data[0] == 'SUCCESS' and len(response_data) > 1 and len(response_data[1]) > 0 and len(response_data[1][0]) > 1 and len(response_data[1][0][1]) > 0:
                    translit_word = response_data[1][0][1][0]
                else:
                    translit_word = word  # fallback to original word
                transliterated_words.append(translit_word)
            else:
                transliterated_words.append(word)
        transliterated_text = ' '.join(transliterated_words)
        app.logger.info(f"Transliteration result: '{transliterated_text}'")
        return jsonify({'transliterated_text': transliterated_text})
    except Exception as e:
        app.logger.error(f"Transliteration error: {str(e)}")
        return jsonify({'error': str(e)})

def get_google_transliteration_code(language):
    """Convert language name/code to Google's transliteration format."""
    mapping = {
        # Full language names
        'hindi': 'hi-t-i0-und',
        'telugu': 'te-t-i0-und',
        'tamil': 'ta-t-i0-und',
        'bengali': 'bn-t-i0-und',
        'marathi': 'mr-t-i0-und',
        'gujarati': 'gu-t-i0-und',
        'kannada': 'kn-t-i0-und',
        'malayalam': 'ml-t-i0-und',
        'punjabi': 'pa-t-i0-und',
        'urdu': 'ur-t-i0-und',
        'odia': 'or-t-i0-und',
        'assamese': 'as-t-i0-und',
        'nepali': 'ne-t-i0-und',
        'sanskrit': 'sa-t-i0-und',
        'sinhalese': 'si-t-i0-und',
        
        # ISO 639-1 codes
        'hi': 'hi-t-i0-und',
        'te': 'te-t-i0-und',
        'ta': 'ta-t-i0-und',
        'bn': 'bn-t-i0-und',
        'mr': 'mr-t-i0-und',
        'gu': 'gu-t-i0-und',
        'kn': 'kn-t-i0-und',
        'ml': 'ml-t-i0-und',
        'pa': 'pa-t-i0-und',
        'ur': 'ur-t-i0-und',
        'or': 'or-t-i0-und',
        'as': 'as-t-i0-und',
        'ne': 'ne-t-i0-und',
        'sa': 'sa-t-i0-und',
        'si': 'si-t-i0-und',
    }
    
    # Handle null or empty language
    if not language:
        language_lower = 'en'
    else:
        # Strip locale part if present (e.g., 'te-IN' -> 'te')
        if '-' in language:
            language = language.split('-')[0]
        
        # Convert to lowercase for case-insensitive matching
        language_lower = language.lower()
    
    # Get the mapped code or default to English
    google_code = mapping.get(language_lower, 'en-t-i0-und')
    
    app.logger.info(f"Language code mapping: {language} → {google_code}")
    return google_code

@app.route('/api/get_translation', methods=['GET'])
def get_translation():
    """Get translation data for editing."""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            print("Error: Session ID is required")
            return jsonify({'error': 'Session ID is required'}), 400
            
        # Load translation data
        translation_path = os.path.join('outputs', session_id, 'diarization_translated.json')
        if not os.path.exists(translation_path):
            print(f"Error: Translation data not found at {translation_path}")
            return jsonify({'error': 'Translation data not found'}), 404
            
        print(f"Loading translation data from {translation_path}")
        with open(translation_path) as f:
            data = json.load(f)
            
        print(f"Translation data loaded successfully with {len(data.get('segments', []))} segments")
        return jsonify(data)
    except Exception as e:
        print(f"Error getting translation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/save_translation', methods=['POST'])
def save_translation():
    """Save edited translation data."""
    try:
        session_id = request.json['session_id']
        updates = request.json['updates']
        
        # Validate session dir exists
        session_dir = os.path.join('outputs', session_id)
        if not os.path.isdir(session_dir):
            return jsonify({'success': False, 'error': 'Invalid session'})
            
        # Create tool_outputs directory if it doesn't exist
        tool_outputs_dir = os.path.join(session_dir, 'tool_outputs')
        os.makedirs(tool_outputs_dir, exist_ok=True)
            
        # Load and update only allowed fields
        translation_path = os.path.join(session_dir, 'diarization_translated.json')
        if not os.path.exists(translation_path):
            return jsonify({'success': False, 'error': 'Translation data not found'})
            
        with open(translation_path) as f:
            data = json.load(f)
            
        # Save original to tool_outputs if it doesn't exist yet
        original_backup_path = os.path.join(tool_outputs_dir, 'diarization_translated_original.json')
        if not os.path.exists(original_backup_path):
            with open(original_backup_path, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved original translated diarization data to {original_backup_path}")
            
        # Update the segments with the edited translations
        for seg_id, changes in updates.items():
            for segment in data['segments']:
                if str(segment['segment_id']) == str(seg_id):
                    if 'translated_text' in changes:
                        segment['translated_text'] = str(changes['translated_text'])
        
        # Atomic write
        temp_path = os.path.join(session_dir, 'diarization_translated.tmp')
        final_path = os.path.join(session_dir, 'diarization_translated.json')
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, final_path)
        
        # Generate merged segments for better TTS alignment
        try:
            print("Generating merged segments for better TTS alignment...")
            from modules.segment_merger import merge_segments
            
            # Merge segments with hardcoded silence threshold
            merged_segments = merge_segments(data['segments'], max_silence_ms=500)
            
            # Create new merged data structure
            merged_data = {
                'transcript': data.get('transcript', ''),
                'translated_transcript': data.get('translated_transcript', ''),
                'merged_segments': merged_segments,
                'original_segment_count': len(data['segments']),
                'merged_segment_count': len(merged_segments),
                'max_silence_ms': 500
            }
            
            # Save merged data
            merged_file = os.path.join(session_dir, 'diarization_translated_merged.json')
            with open(merged_file, 'w') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
            print(f"Successfully merged {len(data['segments'])} segments into {len(merged_segments)} segments")
            
            return jsonify({
                'success': True,
                'segments_merged': True,
                'original_count': len(data['segments']),
                'merged_count': len(merged_segments)
            })
        except Exception as e:
            print(f"Error generating merged segments: {str(e)}")
            # Return success even if merging fails, since translation was saved
            return jsonify({'success': True, 'segments_merged': False, 'merge_error': str(e)})
            
    except Exception as e:
        print(f"Error saving translation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/process_video_url', methods=['POST'])
def process_video_url():
    """
    Process a YouTube or Instagram video URL by extracting its audio.
    """
    try:
        # Add detailed logging
        print("==== VIDEO URL DEBUG ==== Starting /api/process_video_url endpoint")
        
        # Get request data
        request_data = request.get_json() or {}
        form_data = request.form
        
        print(f"Request JSON: {request_data}")
        print(f"Request Form: {form_data}")
        
        # Get video URL
        video_url = request_data.get('video_url') or form_data.get('video_url')
        
        if not video_url:
            print("==== VIDEO URL DEBUG ==== Error: No video URL provided")
            return jsonify({"error": "Video URL is required"}), 400
        
        # Validate URL
        is_valid, platform = is_valid_video_url(video_url)
        if not is_valid:
            print(f"==== VIDEO URL DEBUG ==== Error: Invalid {platform} URL: {video_url}")
            return jsonify({"error": f"Invalid video URL. Please provide a valid YouTube or Instagram URL."}), 400
        
        print(f"==== VIDEO URL DEBUG ==== Valid {platform} URL: {video_url}")
        
        # Generate session ID using the random format (session_XXXXXXXXXX)
        session_id = generate_random_session_id()
        print(f"==== VIDEO URL DEBUG ==== Generated session ID: {session_id}")
        
        # Initialize processing status
        update_processing_status(session_id, "video_processing", "Initializing video processing...", 5)
        
        # Create session directory
        dirs = create_session_directory(session_id)
        print(f"==== VIDEO URL DEBUG ==== Created session directory: {dirs['session_dir']}")
        
        try:
            # Update status - extracting audio
            update_processing_status(session_id, "video_processing", f"Downloading video from {platform}...", 15)
            
            # Extract audio from video URL
            print(f"==== VIDEO URL DEBUG ==== Extracting audio from {platform} URL")
            audio_path = extract_audio_from_url(video_url, session_id, dirs["audio_dir"])
            print(f"==== VIDEO URL DEBUG ==== Audio extracted to: {audio_path}")
            
            # Update status - audio extracted
            update_processing_status(session_id, "video_processing", "Audio successfully extracted from video", 40)
            
            # Save original audio path to session
            session['audio_path'] = audio_path
            session['upload_path'] = audio_path  # Store path with the same key used in audio upload flow
            session['session_id'] = session_id
            
            # Clear any existing transcription data to ensure fresh processing
            session.pop('transcription', None)
            session.pop('diarization', None)
            session.pop('source_language', None)
            session.pop('translation', None)
        except ImportError as e:
            print(f"==== VIDEO URL DEBUG ==== Error: {str(e)}")
            error_message = str(e)
            error_status = "Server configuration error"
            
            if "yt-dlp" in error_message or "yt_dlp" in error_message:
                error_status = "Server configuration error: yt-dlp is not installed"
            elif "pytube" in error_message:
                error_status = "Server configuration error: pytube is not installed"
            else:
                error_status = "Server configuration error: Required package is not installed"
                
            # Update status with error
            update_processing_status(session_id, "error", error_status, 0)
            
            return jsonify({"error": error_status, "details": error_message}), 500
        except RuntimeError as e:
            print(f"==== VIDEO URL DEBUG ==== Error extracting audio: {str(e)}")
            error_message = str(e)
            error_status = f"Failed to extract audio from {platform} video"
            
            if "YouTube is currently blocking automated downloads" in error_message:
                error_status = "YouTube is currently blocking automated downloads. Please try a different video or try again later."
                # Update status with error
                update_processing_status(session_id, "error", error_status, 0)
                return jsonify({"error": error_status}), 429
            else:
                # Update status with error
                update_processing_status(session_id, "error", error_status, 0)
                return jsonify({"error": error_status, "details": error_message}), 500
        except Exception as e:
            print(f"==== VIDEO URL DEBUG ==== Error extracting audio: {str(e)}")
            print(f"==== VIDEO URL DEBUG ==== Traceback: {traceback.format_exc()}")
            error_status = f"Failed to process {platform} video"
            # Update status with error
            update_processing_status(session_id, "error", error_status, 0)
            return jsonify({"error": error_status, "details": str(e)}), 500
            
        # Update metadata
        update_metadata_field(session_id, "source_type", "video_url")
        update_metadata_field(session_id, "video_url", video_url)
        update_metadata_field(session_id, "video_platform", platform)
        update_metadata_field(session_id, "original_audio", audio_path)
        print(f"==== VIDEO URL DEBUG ==== Updated metadata for session: {session_id}")
            
        # Analyze audio components
        try:
            # Update status - analyzing audio
            update_processing_status(session_id, "audio_analysis", "Analyzing audio characteristics...", 50)
            
            print("==== VIDEO URL DEBUG ==== Analyzing audio components")
            audio_analysis = analyze_audio_components(audio_path)
            update_metadata_field(session_id, "audio_analysis", audio_analysis)
            print(f"==== VIDEO URL DEBUG ==== Audio analysis completed: {audio_analysis}")
        except Exception as e:
            print(f"==== VIDEO URL DEBUG ==== Warning: Audio analysis failed: {str(e)}")
            # Non-critical error, continue processing
            
        # Separate vocals from background music
        try:
            # Update status - separating audio
            update_processing_status(session_id, "audio_separation", "Separating speech from background music...", 65)
            
            print(f"==== VIDEO URL DEBUG ==== Starting audio separation for session: {session_id}")
            separation_result = separate_vocals_from_background(
                input_file=audio_path,
                output_dir="outputs",
                session_id=session_id
            )
            
            # Add separation results to metadata
            audio_separation_data = {
                "vocals_path": separation_result["vocals_path"],
                "background_path": separation_result["background_path"],
                "has_significant_background": separation_result["has_significant_background"]
            }
            # Update metadata with audio separation results
            update_metadata_section(session_id, "audio_separation", audio_separation_data)
            
            # Update status based on background music detection
            if separation_result["has_significant_background"]:
                update_processing_status(session_id, "audio_separation", "Background music detected and separated successfully", 80)
                print(f"==== VIDEO URL DEBUG ==== Significant background music detected in the audio")
            else:
                update_processing_status(session_id, "audio_separation", "Audio processing complete - no significant background music detected", 80)
                print(f"==== VIDEO URL DEBUG ==== No significant background music detected in the audio")
                
            print(f"==== VIDEO URL DEBUG ==== Audio separation complete. Background music saved to: {separation_result['background_path']}")
        except Exception as e:
            print(f"==== VIDEO URL DEBUG ==== Error during audio separation: {str(e)}")
            print("==== VIDEO URL DEBUG ==== Continuing with original audio file")
            # Continue with the original audio file if separation fails
            update_processing_status(session_id, "audio_separation", "Audio processing complete (using original audio)", 80)
            
        # Final status update - processing complete
        update_processing_status(session_id, "completed", f"Successfully processed {platform} video", 100)
        
        return jsonify({
            "success": True,
            "message": f"Successfully extracted audio from {platform} video",
            "session_id": session_id,
            "audio_path": audio_path,
            "next_step": "language_detection"
        })
            
    except Exception as e:
        print(f"==== VIDEO URL DEBUG ==== Error extracting audio: {str(e)}")
        import traceback
        print(f"==== VIDEO URL DEBUG ==== Traceback: {traceback.format_exc()}")
        error_status = f"Failed to extract audio: {str(e)}"
        
        # Try to get session_id if available
        try:
            current_session_id = session.get('session_id', None)
            if current_session_id:
                update_processing_status(current_session_id, "error", error_status, 0)
        except:
            pass
            
        return jsonify({"error": error_status}), 500

@app.route('/api/session_files', methods=['GET'])
def get_session_files():
    """
    Get a list of files and directories for a specific session.
    Query parameters:
    - session_id: ID of the session to browse (required)
    - path: Relative path within the session directory (optional)
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
            
        # Base session directory
        base_session_dir = os.path.join('outputs', session_id)
        if not os.path.exists(base_session_dir):
            return jsonify({"error": f"Session {session_id} not found"}), 404
            
        # Get relative path within session directory (if provided)
        rel_path = request.args.get('path', '')
        
        # Ensure the path doesn't try to navigate outside the session directory
        if '..' in rel_path:
            return jsonify({"error": "Invalid path"}), 400
            
        # Full path to browse
        full_path = os.path.join(base_session_dir, rel_path)
        if not os.path.exists(full_path):
            return jsonify({"error": f"Path not found: {rel_path}"}), 404
            
        # List files and directories
        if os.path.isdir(full_path):
            items = []
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                item_type = 'directory' if os.path.isdir(item_path) else 'file'
                item_size = os.path.getsize(item_path) if item_type == 'file' else None
                items.append({
                    'name': item,
                    'type': item_type,
                    'size': item_size,
                    'path': os.path.join(rel_path, item) if rel_path else item
                })
            return jsonify({
                'session_id': session_id,
                'current_path': rel_path,
                'items': items
            })
        else:
            # It's a file, return file info
            return jsonify({
                'session_id': session_id,
                'current_path': rel_path,
                'file_info': {
                    'name': os.path.basename(full_path),
                    'size': os.path.getsize(full_path),
                    'type': 'file'
                }
            })
    except Exception as e:
        print(f"Error in get_session_files: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/session_file_content', methods=['GET'])
def get_session_file_content():
    """
    Get the content of a specific file within a session.
    Query parameters:
    - session_id: ID of the session (required)
    - path: Path to the file within the session directory (required)
    """
    try:
        session_id = request.args.get('session_id')
        file_path = request.args.get('path')
        
        if not session_id or not file_path:
            return jsonify({"error": "Both session_id and path are required"}), 400
            
        # Ensure the path doesn't try to navigate outside the session directory
        if '..' in file_path:
            return jsonify({"error": "Invalid path"}), 400
            
        # Full path to the file
        full_path = os.path.join('outputs', session_id, file_path)
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({"error": f"File not found: {file_path}"}), 404
            
        # Check file extension to determine how to return it
        file_ext = os.path.splitext(full_path)[1].lower()
        
        # For JSON files, parse and return as JSON
        if file_ext == '.json':
            with open(full_path, 'r') as f:
                try:
                    content = json.load(f)
                    return jsonify({
                        'session_id': session_id,
                        'file_path': file_path,
                        'content': content
                    })
                except json.JSONDecodeError:
                    # If JSON parsing fails, return as text
                    with open(full_path, 'r') as f2:
                        content = f2.read()
                    return jsonify({
                        'session_id': session_id,
                        'file_path': file_path,
                        'content': content,
                        'note': 'File could not be parsed as JSON, returning as text'
                    })
        
        # For text files, return content as text
        elif file_ext in ['.txt', '.log', '.py', '.js', '.html', '.css', '.md']:
            with open(full_path, 'r') as f:
                content = f.read()
            return jsonify({
                'session_id': session_id,
                'file_path': file_path,
                'content': content
            })
        
        # For binary files like audio/images, return a URL to download them
        else:
            file_url = f"/outputs/{session_id}/{file_path}"
            return jsonify({
                'session_id': session_id,
                'file_path': file_path,
                'file_url': file_url,
                'note': 'Binary file, use file_url to access content directly'
            })
    except Exception as e:
        print(f"Error in get_session_file_content: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/download_session', methods=['GET'])
def download_session():
    """
    Download all files for a session as a zip archive.
    Query parameters:
    - session_id: ID of the session to download (required)
    """
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
            
        # Base session directory
        session_dir = os.path.join('outputs', session_id)
        if not os.path.exists(session_dir):
            return jsonify({"error": f"Session {session_id} not found"}), 404
            
        # Create a temporary file for the zip
        import tempfile
        import zipfile
        import shutil
        
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, f"{session_id}.zip")
        
        # Create the zip file
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(session_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(session_dir))
                    zipf.write(file_path, arcname)
        
        # Return the zip file
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{session_id}.zip"
        )
    except Exception as e:
        print(f"Error in download_session: {str(e)}")
        return jsonify({"error": str(e)}), 500
 
if __name__ == '__main__':
    # Use PORT environment variable for Cloud Run compatibility
    port = int(os.environ.get('PORT', 5784))
    app.run(debug=True, host='0.0.0.0', port=port)
