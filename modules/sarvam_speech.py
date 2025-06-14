import os
import json
import time
import logging
import tempfile
import asyncio
import aiohttp
import requests
import aiofiles
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from azure.storage.filedatalake.aio import DataLakeDirectoryClient, FileSystemClient
from azure.storage.filedatalake import ContentSettings
import mimetypes
from typing import List, Dict, Any, Optional, Union
from . import vad_segmentation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import secret manager utility
try:
    from utils.secret_manager import get_secret
    
    # Get API key directly from Secret Manager or environment variables
    SARVAM_API_KEY = get_secret('sarvam-api-key', project_id="phonic-bivouac-272213")
    
    if SARVAM_API_KEY:
        logger.info(f"SARVAM_API_KEY loaded successfully with length: {len(SARVAM_API_KEY)}")
    else:
        # Fall back to environment variables if Secret Manager doesn't have the key
        SARVAM_API_KEY = os.environ.get('SARVAM_API_KEY')
        if SARVAM_API_KEY:
            logger.info(f"SARVAM_API_KEY loaded from environment variables with length: {len(SARVAM_API_KEY)}")
        else:
            logger.error("ERROR: SARVAM_API_KEY not found in Secret Manager or environment variables")
            SARVAM_API_KEY = None
            
except ImportError:
    # Fall back to environment variables if secret_manager module is not available
    SARVAM_API_KEY = os.environ.get('SARVAM_API_KEY')
    if SARVAM_API_KEY:
        logger.info(f"Secret Manager not available, using environment variables for SARVAM_API_KEY")
    else:
        logger.error("ERROR: SARVAM_API_KEY not found in environment variables and Secret Manager not available")
        SARVAM_API_KEY = None

# Create a file handler
os.makedirs("logs", exist_ok=True)
file_handler = logging.FileHandler("logs/sarvam_api.log")
file_handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(file_handler)
logger.info(f"Logging to file: {os.path.abspath('logs/sarvam_api.log')}")

class SarvamStorageClient:
    """
    Client for interacting with Azure Data Lake Storage used by Sarvam API.
    Handles file uploads, downloads, and listing operations.
    """
    def __init__(self, url: str):
        """
        Initialize the client with a storage URL from Sarvam API.
        
        Args:
            url (str): The storage URL provided by Sarvam API
        """
        self.account_url, self.file_system_name, self.directory_name, self.sas_token = (
            self._extract_url_components(url)
        )
        self.lock = asyncio.Lock()
        logger.info(f"Initialized SarvamClient with directory: {self.directory_name}")

    def update_url(self, url: str):
        """
        Update the storage URL.
        
        Args:
            url (str): The new storage URL
        """
        self.account_url, self.file_system_name, self.directory_name, self.sas_token = (
            self._extract_url_components(url)
        )
        logger.info(f"Updated URL to directory: {self.directory_name}")

    def _extract_url_components(self, url: str):
        """
        Extract components from the Azure Storage URL.
        
        Args:
            url (str): The storage URL
            
        Returns:
            tuple: (account_url, file_system_name, directory_name, sas_token)
        """
        parsed_url = urlparse(url)
        # Convert blob URL to dfs URL for Data Lake Storage
        account_url = f"{parsed_url.scheme}://{parsed_url.netloc}".replace(
            ".blob.", ".dfs."
        )
        path_components = parsed_url.path.strip("/").split("/")
        file_system_name = path_components[0]
        directory_name = "/".join(path_components[1:])
        sas_token = parsed_url.query
        
        logger.debug(f"Extracted URL components: account_url={account_url}, file_system={file_system_name}, directory={directory_name}")
        return account_url, file_system_name, directory_name, sas_token

    async def upload_file(self, local_file_path, overwrite=True):
        """
        Upload a file to Azure Data Lake Storage.
        
        Args:
            local_file_path (str): Path to the local file
            overwrite (bool): Whether to overwrite existing files
            
        Returns:
            bool: True if upload was successful, False otherwise
        """
        file_name = os.path.basename(local_file_path)
        logger.info(f"Uploading file: {file_name} from {local_file_path}")
        
        try:
            async with DataLakeDirectoryClient(
                account_url=f"{self.account_url}?{self.sas_token}",
                file_system_name=self.file_system_name,
                directory_name=self.directory_name,
                credential=None,
            ) as directory_client:
                async with aiofiles.open(local_file_path, mode="rb") as file_data:
                    mime_type = mimetypes.guess_type(local_file_path)[0] or "audio/wav"
                    file_client = directory_client.get_file_client(file_name)
                    data = await file_data.read()
                    await file_client.upload_data(
                        data,
                        overwrite=overwrite,
                        content_settings=ContentSettings(content_type=mime_type),
                    )
                    logger.info(f"File uploaded successfully: {file_name}")
                    return True
        except Exception as e:
            logger.error(f"Upload failed for {file_name}: {str(e)}")
            return False

    async def list_files(self):
        """
        List files in the directory.
        
        Returns:
            list: List of file names
        """
        logger.info(f"Listing files in directory: {self.directory_name}")
        file_names = []
        
        try:
            async with FileSystemClient(
                account_url=f"{self.account_url}?{self.sas_token}",
                file_system_name=self.file_system_name,
                credential=None,
            ) as file_system_client:
                async for path in file_system_client.get_paths(self.directory_name):
                    file_name = path.name.split("/")[-1]
                    if file_name:  # Skip empty names (directories)
                        file_names.append(file_name)
                        logger.debug(f"Found file: {file_name}")
            
            logger.info(f"Found {len(file_names)} files")
            return file_names
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []

    async def download_files(self, file_names, destination_dir):
        """
        Download multiple files from Azure Data Lake Storage.
        
        Args:
            file_names (list): List of file names to download
            destination_dir (str): Local directory to save files
            
        Returns:
            list: List of paths to downloaded files
        """
        logger.info(f"Downloading {len(file_names)} files to {destination_dir}")
        downloaded_files = []
        
        try:
            async with DataLakeDirectoryClient(
                account_url=f"{self.account_url}?{self.sas_token}",
                file_system_name=self.file_system_name,
                directory_name=self.directory_name,
                credential=None,
            ) as directory_client:
                for file_name in file_names:
                    try:
                        file_client = directory_client.get_file_client(file_name)
                        download_path = os.path.join(destination_dir, file_name)
                        
                        # Create directory if it doesn't exist
                        os.makedirs(os.path.dirname(download_path), exist_ok=True)
                        
                        # Download the file
                        with open(download_path, mode="wb") as file_data:
                            stream = await file_client.download_file()
                            data = await stream.readall()
                            file_data.write(data)
                            
                        logger.info(f"Downloaded: {file_name} to {download_path}")
                        downloaded_files.append(download_path)
                    except Exception as e:
                        logger.error(f"Download failed for {file_name}: {str(e)}")
            
            return downloaded_files
        except Exception as e:
            logger.error(f"Error in download_files: {str(e)}")
            return downloaded_files

async def initialize_job(api_key=None):
    """
    Initialize a new batch job for speech-to-text processing.
    
    Args:
        api_key (str, optional): Sarvam API key. If None, uses the module-level SARVAM_API_KEY.
        
    Returns:
        dict: Job information including job_id and storage paths
    """
    logger.info("Initializing Sarvam batch job...")
    
    # Use module-level API key if none provided
    if api_key is None:
        api_key = SARVAM_API_KEY
        logger.info("Using module-level SARVAM_API_KEY")
            
    if not api_key:
        error_msg = "No API key available for Sarvam API"
        logger.error(error_msg)
        return None
        
    # Log API key info for debugging
    logger.info(f"API key is present with length: {len(api_key)}")
    logger.info(f"First 4 chars of API key: {api_key[:4]}")
    
    url = 'https://api.sarvam.ai/speech-to-text/job/init'
    headers = {'API-Subscription-Key': api_key}
    
    try:
        # Log the full request details for debugging
        logger.info(f"Making request to URL: {url}")
        logger.info(f"Headers: {{'API-Subscription-Key': '[REDACTED]'}}")
        
        response = requests.post(url, headers=headers)
        
        # Log the response details
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 202:
            job_info = response.json()
            logger.info(f"Job initialized successfully: {job_info['job_id']}")
            return job_info
        else:
            logger.error(f"Failed to initialize job: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error initializing job: {str(e)}")
        return None

async def check_job_status(job_id, api_key=None):
    """
    Check the status of a batch job.
    
    Args:
        job_id (str): Job ID
        api_key (str, optional): Sarvam API key. If None, uses the module-level SARVAM_API_KEY.
        
    Returns:
        dict: Job status information
    """
    logger.info(f"Checking status for job: {job_id}")
    
    # Use module-level API key if none provided
    if api_key is None:
        api_key = SARVAM_API_KEY
        logger.info("Using module-level SARVAM_API_KEY for status check")
            
    if not api_key:
        error_msg = "No API key available for Sarvam API"
        logger.error(error_msg)
        return None
        
    url = f'https://api.sarvam.ai/speech-to-text/job/{job_id}/status'
    headers = {'API-Subscription-Key': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            status_data = response.json()
            logger.info(f"Current job status: {status_data['job_state']}")
            return status_data
        else:
            logger.error(f"Failed to check job status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
        return None

async def start_job(job_id, api_key=None, with_diarization=True):
    """
    Start a batch job for processing.
    
    Args:
        job_id (str): Job ID
        api_key (str, optional): Sarvam API key. If None, uses the module-level SARVAM_API_KEY.
        with_diarization (bool): Whether to enable speaker diarization
        
    Returns:
        dict: Response from the API
    """
    logger.info(f"Starting job: {job_id}")
    
    # Use module-level API key if none provided
    if api_key is None:
        api_key = SARVAM_API_KEY
        logger.info("Using module-level SARVAM_API_KEY for job start")
            
    if not api_key:
        error_msg = "No API key available for Sarvam API"
        logger.error(error_msg)
        return None
    
    # Try the original endpoint format without job_id in the URL
    url = 'https://api.sarvam.ai/speech-to-text/job'
    headers = {
        'API-Subscription-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Format the data according to the API documentation
    data = {
        "job_id": job_id,
        "job_parameters": {
            "model": "saarika:v2",
            "with_diarization": with_diarization,
            "with_timestamps": True
        }
    }
    
    logger.info(f"Starting job with diarization: {with_diarization}")
    logger.info(f"API endpoint: {url}")
    logger.info(f"Request data: {json.dumps(data)}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logger.info("Job started successfully")
            return response.json()
        else:
            # If the first attempt fails, try the alternative endpoint format
            alt_url = f'https://api.sarvam.ai/speech-to-text/job/{job_id}/start'
            alt_data = {
                "model": "saarika:v2",
                "diarize": "true" if with_diarization else "false"
            }
            
            logger.info(f"First attempt failed. Trying alternative endpoint: {alt_url}")
            logger.info(f"Alternative request data: {json.dumps(alt_data)}")
            
            alt_response = requests.post(alt_url, headers=headers, json=alt_data)
            
            if alt_response.status_code == 200:
                logger.info("Job started successfully with alternative endpoint")
                return alt_response.json()
            else:
                logger.error(f"Failed to start job with both endpoints. Original: {response.status_code} - {response.text}, Alternative: {alt_response.status_code} - {alt_response.text}")
    except Exception as e:
        logger.error(f"Error starting job: {str(e)}")
        return None

async def get_job_results(job_id, api_key=None):
    """
    Get the results of a completed job directly from the API.
    
    Args:
        job_id (str): Job ID
        api_key (str, optional): Sarvam API key. If None, uses the module-level SARVAM_API_KEY.
        
    Returns:
        dict: Job results
    """
    logger.info(f"Getting results for job: {job_id}")
    
    # Use module-level API key if none provided
    if api_key is None:
        api_key = SARVAM_API_KEY
        logger.info("Using module-level SARVAM_API_KEY for getting results")
            
    if not api_key:
        error_msg = "No API key available for Sarvam API"
        logger.error(error_msg)
        return None
    
    url = f'https://api.sarvam.ai/speech-to-text/job/{job_id}/results'
    headers = {'API-Subscription-Key': api_key}
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            logger.info("Successfully retrieved job results")
            return response.json()
        else:
            logger.error(f"Failed to get job results: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error getting job results: {str(e)}")
        return None

async def process_audio_with_diarization(audio_path, api_key=None):
    """
    Process an audio file with speaker diarization using Sarvam's Batch API.
    
    Args:
        audio_path (str): Path to the audio file
        api_key (str, optional): Sarvam API key. If None, uses the module-level SARVAM_API_KEY.
        
    Returns:
        dict: Processed results with transcription and diarization
    """
    logger.info(f"Processing audio with diarization: {audio_path}")
    
    # Use module-level API key if none provided
    if api_key is None:
        api_key = SARVAM_API_KEY
        logger.info("Using module-level SARVAM_API_KEY for audio processing")
            
    if not api_key:
        error_msg = "No API key available for Sarvam API"
        logger.error(error_msg)
        return {"error": error_msg}
    
    # Step 1: Initialize job
    job_info = await initialize_job(api_key)
    if not job_info:
        logger.error("Failed to initialize job")
        return {"error": "Failed to initialize job"}
    
    job_id = job_info['job_id']
    input_storage_path = job_info['input_storage_path']
    output_storage_path = job_info['output_storage_path']
    
    # Step 2: Upload audio file
    logger.info(f"Uploading audio file to: {input_storage_path}")
    input_client = SarvamStorageClient(input_storage_path)
    upload_success = await input_client.upload_file(audio_path)
    
    if not upload_success:
        logger.error("Failed to upload audio file")
        return {"error": "Failed to upload audio file"}
    
    # Step 3: Start the job
    start_response = await start_job(job_id, api_key, with_diarization=True)
    if not start_response:
        logger.error("Failed to start job")
        return {"error": "Failed to start job"}
    
    # Step 4: Monitor job status
    logger.info("Monitoring job status...")
    max_attempts = 30
    for attempt in range(1, max_attempts + 1):
        logger.debug(f"Status check attempt {attempt}/{max_attempts}")
        
        job_status = await check_job_status(job_id, api_key)
        if not job_status:
            logger.error("Failed to check job status")
            return {"error": "Failed to check job status"}
        
        status = job_status['job_state']
        if status == 'Completed':
            logger.info("Job completed successfully!")
            break
        elif status == 'Failed':
            error_message = job_status.get('error_message', 'Unknown error')
            logger.error(f"Job failed: {error_message}")
            return {"error": f"Job failed: {error_message}"}
        else:
            logger.info(f"Job status: {status}. Waiting...")
            await asyncio.sleep(5)  # Wait 5 seconds before checking again
    
    # Step 5: Get results
    # First try to get results directly from the API
    results = await get_job_results(job_id, api_key)
    if results:
        logger.info("Successfully retrieved results from API")
        return results
    
    # If direct API results fail, try downloading from storage
    logger.info(f"Using output storage path from job status: {output_storage_path}")
    output_client = SarvamStorageClient(output_storage_path)
    
    # Create a temporary directory for downloaded files
    with tempfile.TemporaryDirectory() as temp_dir:
        # List files in the output directory
        output_files = await output_client.list_files()
        
        if not output_files:
            logger.error("No output files found")
            return {"error": "No output files found"}
        
        # Download the files
        downloaded_files = await output_client.download_files(output_files, temp_dir)
        
        if not downloaded_files:
            logger.error("Failed to download output files")
            return {"error": "Failed to download output files"}
        
        # Process the downloaded files
        results = {}
        for file_path in downloaded_files:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    file_results = json.load(f)
                    # Save raw results for debugging
                    debug_path = f"/tmp/sarvam_raw_{os.path.basename(file_path)}"
                    with open(debug_path, 'w') as debug_file:
                        json.dump(file_results, debug_file, indent=2)
                    logger.info(f"Saved raw API response to {debug_path}")
                    results.update(file_results)
        
        if not results:
            logger.error("No valid results found in downloaded files")
            return {"error": "No valid results found in downloaded files"}
        
        return results

async def transcribe_with_diarization(audio_path, api_key=None):
    """
    Transcribe audio with speaker diarization.
    
    Args:
        audio_path (str): Path to the audio file
        api_key (str, optional): Sarvam API key. If None, uses the module-level SARVAM_API_KEY.
        
    Returns:
        dict: Transcription results with speaker diarization
    """
    logger.info(f"Transcribing with diarization: {audio_path}")
    
    # Use module-level API key if none provided
    if api_key is None:
        api_key = SARVAM_API_KEY
        logger.info("Using module-level SARVAM_API_KEY for diarization")
    
    try:
        # Process audio with diarization
        results = await process_audio_with_diarization(audio_path, api_key)
        
        # Check if results contain an error
        if "error" in results:
            logger.error(f"Error in transcription: {results['error']}")
            return {"success": False, "error": results["error"]}
        
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
        
        logger.info(f"Transcription completed successfully: {formatted_result['transcription'][:100]}...")
        return formatted_result
        
    except Exception as e:
        logger.error(f"Error transcribing with diarization: {str(e)}")
        return {"success": False, "error": str(e)}

async def transcribe_with_vad_diarization(audio_path, api_key=None, vad_segments_dir=None, min_segment_duration=1.0):
    """
    Transcribe audio with VAD-based segmentation and diarization.
    
    Args:
        audio_path (str): Path to the audio file
        api_key (str, optional): Sarvam API key. If None, uses the module-level SARVAM_API_KEY.
        vad_segments_dir (str, optional): Directory to save VAD segments
        min_segment_duration (float, optional): Minimum duration for VAD segments
        
    Returns:
        dict: Processed results with transcription and diarization
    """
    
    # Use module-level API key if none provided
    if api_key is None:
        api_key = SARVAM_API_KEY
        logger.info("Using module-level SARVAM_API_KEY for VAD diarization")
            
    if not api_key:
        error_msg = "No API key available for Sarvam API"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    from modules.vad_segmentation import segment_audio_with_vad
    
    logger.info(f"Transcribing with VAD and diarization: {audio_path}")
    
    # Extract session_id from audio path
    session_id = os.path.basename(audio_path).split('.')[0]
    
    # Create a directory for VAD segments if not provided
    if not vad_segments_dir:
        vad_segments_dir = os.path.join('outputs', session_id, 'vad_segments')
    
    logger.info(f"Using provided directory for VAD segments: {vad_segments_dir}")
    os.makedirs(vad_segments_dir, exist_ok=True)
    
    # Segment audio using VAD
    segments = segment_audio_with_vad(
        audio_path=audio_path, 
        output_dir=vad_segments_dir,
        min_segment_duration=min_segment_duration  # Pass min_segment_duration as a separate parameter
    )
    
    # Process each segment with diarization
    segment_results = []
    for i, segment_info in enumerate(segments):
        segment_id = f"seg_{i+1:03d}"
        segment_path = os.path.join(vad_segments_dir, f"segment_{i:03d}.wav")
        
        logger.info(f"Processing segment {segment_id} with diarization")
        try:
            # Pass the same API key to maintain consistency
            segment_result = await process_audio_with_diarization(segment_path, api_key)
            
            # Add segment metadata
            segment_result['segment_id'] = segment_id
            segment_result['start_time'] = segment_info['start_time']
            segment_result['end_time'] = segment_info['end_time']
            
            segment_results.append(segment_result)
            logger.info(f"Successfully processed segment {segment_id}")
        except Exception as e:
            logger.error(f"Error processing segment {segment_id}: {str(e)}")
            segment_results.append({"error": str(e), "segment_id": segment_id})
    
    # Combine results from all segments
    combined_results = combine_segment_results(segment_results)
    
    # Save the diarization results to the expected path
    session_dir = os.path.join("outputs", session_id)
    os.makedirs(session_dir, exist_ok=True)
    diarization_path = os.path.join(session_dir, "diarization.json")
    with open(diarization_path, 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=2)
    logger.info(f"Saved diarization results to: {diarization_path}")
    
    return combined_results

def combine_segment_results(segment_results):
    """
    Combine results from multiple audio segments into a single result.
    
    Args:
        segment_results (list): List of results from individual segments
        
    Returns:
        dict: Combined results
    """
    combined_transcript = ""
    combined_segments = []
    language_code = None
    
    for result in segment_results:
        # Process each segment result
        processed_result = process_diarization_results(result)
        
        # Skip segments with errors
        if 'error' in processed_result:
            logger.error(f"Error in results: {processed_result['error']}")
            continue
        
        # Extract transcript and segments
        transcript = processed_result.get('transcript', '')
        segments = processed_result.get('segments', [])
        
        if not language_code and 'language_code' in processed_result:
            language_code = processed_result['language_code']
        
        # Add transcript to combined transcript
        if transcript:
            if combined_transcript:
                combined_transcript += " " + transcript
            else:
                combined_transcript = transcript
        
        # Adjust segment timestamps based on segment start time
        segment_start = result.get('start_time', 0)
        for i, segment in enumerate(segments):
            # Create a properly structured segment with consistent key names
            adjusted_segment = {
                'segment_id': f"seg_{len(combined_segments):03d}",
                'speaker': segment.get('speaker', f"SPEAKER_{i % 2:02d}"),
                'text': segment.get('text', ''),
                'start_time': segment.get('start_time', 0) + segment_start,
                'end_time': segment.get('end_time', 0) + segment_start,
                'gender': segment.get('gender', 'unknown'),
                'pace': segment.get('pace', 1.0)
            }
            
            # Add duration field calculated from start_time and end_time
            adjusted_segment['duration'] = adjusted_segment['end_time'] - adjusted_segment['start_time']
            
            combined_segments.append(adjusted_segment)
    
    # Create combined result
    combined_result = {
        'transcript': combined_transcript,
        'segments': combined_segments
    }
    
    if language_code:
        combined_result['language_code'] = language_code
    
    logger.info(f"Combined {len(segment_results)} segments into final result with {len(combined_segments)} speaker segments")
    
    return combined_result

def process_diarization_results(results):
    """
    Process the diarization results from Sarvam API.
    
    Args:
        results (dict): Raw results from the API
        
    Returns:
        dict: Processed results with transcription and diarization
    """
    logger.info("Processing diarization results")
    
    try:
        # Check if results is None or empty
        if not results:
            logger.error("Empty results received")
            return {"error": "Empty results received from API"}
            
        # Check if results already contains an error
        if "error" in results:
            logger.error(f"Error in results: {results['error']}")
            return results
            
        # Extract language code if available
        language_code = results.get('language_code', None)
        
        # Debug: Log the raw results structure
        logger.info(f"Raw API response keys: {list(results.keys())}")
        
        # Check if results contain the expected structure
        if 'transcript' in results:
            # New format with transcript at the top level
            transcript = results['transcript']
            
            # Check for diarized_transcript in the new format
            if 'diarized_transcript' in results and 'entries' in results['diarized_transcript']:
                # Extract segments from the new diarized_transcript format
                segments = []
                for entry in results['diarized_transcript']['entries']:
                    segments.append({
                        'speaker': entry.get('speaker_id', 'SPEAKER_00'),
                        'text': entry.get('transcript', ''),
                        'start_time': entry.get('start_time_seconds', 0),
                        'end_time': entry.get('end_time_seconds', 0)
                    })
            else:
                # Look for segments in the old format
                segments = results.get('segments', [])
            
            # If we have transcript but no segments, create a default segment
            if transcript and not segments:
                logger.warning("Transcript found but no segments, creating a default segment")
                segments = [{
                    'speaker': 'SPEAKER_00',
                    'text': transcript,
                    'start_time': 0,
                    'end_time': 100  # Arbitrary end time
                }]
            
            # Process segments for diarization
            processed_segments = []
            for segment in segments:
                start_time = segment.get('start_time', 0)
                end_time = segment.get('end_time', 0)
                processed_segment = {
                    'speaker': segment.get('speaker', 'unknown'),
                    'text': segment.get('text', ''),
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': end_time - start_time  # Add duration field
                }
                processed_segments.append(processed_segment)
            
            return {
                'transcript': transcript,
                'segments': processed_segments,
                'language_code': language_code
            }
        
        # Check for older format
        elif 'results' in results and isinstance(results['results'], list):
            # Old format with results array
            transcript = ""
            processed_segments = []
            
            for result in results['results']:
                if 'transcript' in result:
                    transcript += result['transcript'] + " "
                
                if 'segments' in result:
                    for segment in result['segments']:
                        processed_segments.append({
                            'speaker': segment.get('speaker', 'unknown'),
                            'text': segment.get('text', ''),
                            'start_time': segment.get('start', 0),
                            'end_time': segment.get('end', 0),
                            'duration': segment.get('end', 0) - segment.get('start', 0)  # Add duration field
                        })
            
            # If we have transcript but no segments, create a default segment
            if transcript and not processed_segments:
                logger.warning("Transcript found but no segments in results array, creating a default segment")
                processed_segments = [{
                    'speaker': 'SPEAKER_00',
                    'text': transcript.strip(),
                    'start_time': 0,
                    'end_time': 100,  # Arbitrary end time
                    'duration': 100  # Add duration field
                }]
            
            return {
                'transcript': transcript.strip(),
                'segments': processed_segments,
                'language_code': language_code
            }
        
        else:
            # Unknown format, log the raw results for debugging
            logger.warning(f"Unknown result format: {json.dumps(results, indent=2)}")
            # Try to extract any useful information
            if isinstance(results, dict):
                transcript = results.get('text', '')
                if not transcript and 'transcript' in results:
                    transcript = results['transcript']
                
                return {
                    'transcript': transcript,
                    'segments': [{
                        'speaker': 'SPEAKER_00',
                        'text': transcript,
                        'start_time': 0,
                        'end_time': 100,  # Arbitrary end time
                        'duration': 100  # Add duration field
                    }] if transcript else [],
                    'language_code': language_code
                }
            else:
                return {"error": "Unrecognized result format from API"}
    
    except Exception as e:
        logger.error(f"Error processing diarization results: {str(e)}")
        return {"error": f"Error processing results: {str(e)}"}

def sarvam_synthesize(text: str, language: str, output_path: str, model: str = "bulbul:v2", speaker: Optional[str] = None) -> bool:
    """
    Synthesize text to speech using Sarvam API.
    
    Args:
        text: Text to synthesize
        language: Target language code
        output_path: Path to save the output audio
        model: TTS model to use
        speaker: Optional speaker voice ID
        
    Returns:
        bool: Success status
    """
    try:
        # Use module-level API key
        api_key = SARVAM_API_KEY
        
        if not api_key:
            logger.error("SARVAM_API_KEY not available at module level")
            return False

        # Prepare request data
        request_data = {
            "text": text,
            "language": language,
            "model": model
        }
        
        if speaker:
            request_data["speaker"] = speaker

        # Make API request
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"Synthesizing text with Sarvam: {text[:50]}...")
        
        try:
            response = requests.post(
                url,
                json=request_data,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            # Save the audio to output path
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully synthesized audio to {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error synthesizing text: {e}")
            logger.error(f"Response: {response.text if hasattr(response, 'text') else 'No response'}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error in sarvam_synthesize: {e}")
        return False
