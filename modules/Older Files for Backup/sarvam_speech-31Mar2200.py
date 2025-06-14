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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

async def initialize_job(api_key):
    """
    Initialize a new batch job for speech-to-text processing.
    
    Args:
        api_key (str): Sarvam API key
        
    Returns:
        dict: Job information including job_id and storage paths
    """
    logger.info("Initializing Sarvam batch job...")
    url = 'https://api.sarvam.ai/speech-to-text/job/init'
    headers = {'API-Subscription-Key': api_key}
    
    try:
        response = requests.post(url, headers=headers)
        
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

async def check_job_status(job_id, api_key):
    """
    Check the status of a batch job.
    
    Args:
        job_id (str): Job ID
        api_key (str): Sarvam API key
        
    Returns:
        dict: Job status information
    """
    logger.info(f"Checking status for job: {job_id}")
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

async def start_job(job_id, api_key, with_diarization=True):
    """
    Start a batch job for processing.
    
    Args:
        job_id (str): Job ID
        api_key (str): Sarvam API key
        with_diarization (bool): Whether to enable speaker diarization
        
    Returns:
        dict: Response from the API
    """
    logger.info(f"Starting job: {job_id}")
    url = 'https://api.sarvam.ai/speech-to-text/job'
    headers = {
        'API-Subscription-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    data = {
        "job_id": job_id,
        "job_parameters": {
            "model": "saarika:v2",
            "with_diarization": with_diarization,
            "with_timestamps": True
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            logger.info("Job started successfully")
            return response.json()
        else:
            logger.error(f"Failed to start job: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error starting job: {str(e)}")
        return None

async def get_job_results(job_id, api_key):
    """
    Get the results of a completed job directly from the API.
    
    Args:
        job_id (str): Job ID
        api_key (str): Sarvam API key
        
    Returns:
        dict: Job results
    """
    logger.info(f"Getting results for job: {job_id}")
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

async def process_audio_with_diarization(audio_path, api_key):
    """
    Process an audio file with speaker diarization using Sarvam's Batch API.
    
    Args:
        audio_path (str): Path to the audio file
        api_key (str): Sarvam API key
        
    Returns:
        dict: Processed results with transcription and diarization
    """
    logger.info(f"Processing audio with diarization: {audio_path}")
    
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
        return process_diarization_results(results)
    
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
                    results.update(file_results)
        
        if not results:
            logger.error("No valid results found in downloaded files")
            return {"error": "No valid results found in downloaded files"}
        
        return process_diarization_results(results)

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
        # Extract language code if available
        language_code = results.get('language_code', None)
        
        # Check if results contain the expected structure
        if 'transcript' in results:
            # New format with transcript at the top level
            transcript = results['transcript']
            segments = results.get('segments', [])
            
            # Process segments for diarization
            processed_segments = []
            for segment in segments:
                processed_segments.append({
                    'speaker': segment.get('speaker', 'unknown'),
                    'text': segment.get('text', ''),
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0)
                })
            
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
                            'start': segment.get('start', 0),
                            'end': segment.get('end', 0)
                        })
            
            return {
                'transcript': transcript.strip(),
                'segments': processed_segments,
                'language_code': language_code
            }
        
        else:
            # Unknown format, return as is
            logger.warning("Unknown result format, returning raw results")
            return results
    
    except Exception as e:
        logger.error(f"Error processing diarization results: {str(e)}")
        return {"error": f"Error processing results: {str(e)}", "raw_results": results}

async def transcribe_with_diarization(audio_path, api_key):
    """
    Transcribe audio with speaker diarization.
    
    Args:
        audio_path (str): Path to the audio file
        api_key (str): Sarvam API key
        
    Returns:
        dict: Transcription results with speaker diarization
    """
    logger.info(f"Transcribing with diarization: {audio_path}")
    
    # Process the audio file
    results = await process_audio_with_diarization(audio_path, api_key)
    
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
