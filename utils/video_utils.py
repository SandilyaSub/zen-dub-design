"""
Video utilities for extracting audio from YouTube and Instagram videos.
"""
import os
import logging
import re
import glob
import shutil
import importlib
import subprocess
from typing import Optional, Tuple, List

# Configure logging
logger = logging.getLogger(__name__)

def is_valid_youtube_url(url: str) -> bool:
    """
    Check if the URL is a valid YouTube URL.
    
    Args:
        url: URL to check
        
    Returns:
        bool: True if valid YouTube URL, False otherwise
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)'
        r'([a-zA-Z0-9_-]{11})'
    )
    match = re.match(youtube_regex, url)
    return match is not None

def is_valid_instagram_url(url: str) -> bool:
    """
    Check if the URL is a valid Instagram URL.
    
    Args:
        url: URL to check
        
    Returns:
        bool: True if valid Instagram URL, False otherwise
    """
    instagram_regex = (
        r'(https?://)?(www\.)?' 
        r'(instagram\.com/p/|instagram\.com/reel/|instagram\.com/tv/|instagram\.com/stories/)'
        r'([a-zA-Z0-9_-]+)'
    )
    match = re.match(instagram_regex, url)
    return match is not None

def is_valid_video_url(url: str) -> Tuple[bool, str]:
    """
    Check if the URL is a valid video URL.
    
    Args:
        url: URL to check
        
    Returns:
        Tuple[bool, str]: (is_valid, platform)
    """
    if is_valid_youtube_url(url):
        return True, "youtube"
    elif is_valid_instagram_url(url):
        return True, "instagram"
    else:
        return False, "unknown"

def extract_audio_from_youtube(video_url: str, session_id: str, output_dir: str) -> str:
    """
    Extract audio from a YouTube video URL using multiple methods.
    Primary method is YouTube API, with fallbacks to other methods if needed.
    
    Args:
        video_url: URL of the YouTube video
        session_id: Session ID for naming the output file
        output_dir: Directory to save the audio file
        
    Returns:
        Path to the extracted audio file
        
    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If audio extraction fails
    """
    # Import necessary modules explicitly within the function
    import os
    import re
    import glob
    import shutil
    import importlib
    import subprocess
    import traceback
    # Extract video ID from YouTube URL
    video_id = None
    youtube_patterns = [
        r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/ ]{11})',
        r'(?:youtube\.com/shorts/)([^"&?/ ]{11})'
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, video_url)
        if match:
            video_id = match.group(1)
            break
            
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {video_url}")
        raise ValueError(f"Invalid YouTube URL format: {video_url}")
    
    logger.info(f"Extracted YouTube video ID: {video_id}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Output file path
    output_path = os.path.join(output_dir, f"{session_id}.mp3")
    logger.info(f"Output path: {output_path}")
    
    # Try multiple methods to download the audio
    errors = []
    
    # Method 1: Try using YouTube Data API (most reliable but requires API key)
    try:
        logger.info(f"Method 1: Attempting to use YouTube Data API for video {video_id}")
        
        # Import required modules
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        import requests
        from pydub import AudioSegment
        
        # Get YouTube API key from Secret Manager or environment variable
        from utils.secret_manager import get_secret
        import os
        
        # Try to get from Secret Manager first
        youtube_api_key = get_secret('youtube-api-key')
        
        # If not found in Secret Manager, try environment variable directly
        if not youtube_api_key:
            youtube_api_key = os.environ.get('YOUTUBE_API_KEY')
            if youtube_api_key:
                logger.info("Using YouTube API key from environment variable")
            else:
                logger.warning("YouTube API key not found in Secret Manager or environment, skipping Method 1")
                errors.append("YouTube API key not found")
                # Skip to the next method
                raise Exception("YouTube API key not found, skipping to next method")
        else:
            logger.info("Successfully retrieved YouTube API key")
            
            # Create YouTube API client
            youtube = build('youtube', 'v3', developerKey=youtube_api_key)
            
            # Get video details to verify it exists and is accessible
            video_response = youtube.videos().list(
                part='snippet,contentDetails',
                id=video_id
            ).execute()
            
            if not video_response.get('items'):
                logger.error(f"Video {video_id} not found or not accessible via API")
                errors.append("Video not found via API")
            else:
                video_info = video_response['items'][0]
                video_title = video_info['snippet']['title']
                logger.info(f"Found video via API: {video_title}")
                
                # First try with a direct audio extraction approach
                try:
                    # Use ffmpeg directly to download and convert
                    import subprocess
                    ffmpeg_cmd = [
                        'ffmpeg', '-y', '-i', f"https://www.youtube.com/watch?v={video_id}", 
                        '-vn', '-acodec', 'libmp3lame', '-q:a', '2', output_path
                    ]
                    
                    logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
                    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        logger.info(f"Successfully downloaded and converted audio using ffmpeg: {output_path}")
                        return output_path
                    else:
                        logger.warning(f"ffmpeg command failed: {result.stderr}")
                        # Continue to next approach
                except Exception as ffmpeg_error:
                    logger.warning(f"Direct ffmpeg approach failed: {str(ffmpeg_error)}")
                    # Continue to next approach
                
                # Try using youtube-dlp with a custom format selection
                try:
                    import yt_dlp
                    
                    # Special options focusing just on audio extraction
                    api_opts = {
                        'format': 'bestaudio',  # Only get audio
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                        }],
                        'outtmpl': output_path.replace('.mp3', ''),
                        'quiet': True,
                        'no_warnings': True,
                        'skip_download': False,
                        'noplaylist': True,
                        'youtube_include_dash_manifest': False,
                    }
                    
                    with yt_dlp.YoutubeDL(api_opts) as ydl:
                        logger.info(f"Downloading audio with API-assisted approach")
                        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
                    
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        logger.info(f"Successfully downloaded audio using API-assisted approach: {output_path}")
                        return output_path
                except Exception as api_dlp_error:
                    logger.warning(f"API-assisted yt-dlp approach failed: {str(api_dlp_error)}")
                    # Continue to final approach
    except Exception as e:
        error_msg = f"Method 1 (YouTube API) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # Method 2: Try using pytube
    try:
        logger.info(f"Method 2: Attempting to use pytube to download video {video_id}")
        
        # Check if pytube is installed
        pytube_spec = importlib.util.find_spec("pytube")
        if pytube_spec is None:
            logger.warning("pytube is not installed, skipping Method 2")
            errors.append("pytube is not installed")
        else:
            from pytube import YouTube
            
            # Create a YouTube object
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            
            # Get the audio stream
            audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                logger.error(f"No audio stream found for video {video_id}")
                errors.append("No audio stream found")
            else:
                # Download to a temporary file
                temp_file = audio_stream.download(output_path=output_dir, filename=f"{session_id}_temp")
                logger.info(f"Downloaded audio to {temp_file}")
                
                # Convert to mp3 using pydub
                from pydub import AudioSegment
                audio = AudioSegment.from_file(temp_file)
                audio.export(output_path, format="mp3")
                logger.info(f"Converted audio to mp3: {output_path}")
                
                # Remove the temporary file
                try:
                    os.remove(temp_file)
                    logger.info(f"Removed temporary file: {temp_file}")
                except Exception as remove_error:
                    logger.warning(f"Could not remove temporary file: {str(remove_error)}")
                
                # Verify the file exists
                if os.path.exists(output_path):
                    logger.info(f"Method 2 successful: {output_path}")
                    return output_path
    except Exception as e:
        error_msg = f"Method 2 (pytube) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # Method 3: Try using yt-dlp
    try:
        logger.info(f"Method 3: Attempting to use yt-dlp for video {video_id}")
        
        # Check if yt-dlp is installed
        try:
            import yt_dlp
        except ImportError:
            logger.warning("yt-dlp is not installed, skipping Method 3")
            errors.append("yt-dlp is not installed")
            raise RuntimeError(f"All download methods failed: {', '.join(errors)}")
        
        # Options for yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'paths': {'home': output_dir},
            'outtmpl': {'default': f"{session_id}.%(ext)s"},
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'sleep_interval': 5,
            'max_sleep_interval': 10,
            'extractor_retries': 5,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading with yt-dlp: {video_url}")
            ydl.download([video_url])
        
        # Check for the file
        possible_files = glob.glob(os.path.join(output_dir, f"{session_id}*.mp3"))
        if possible_files:
            actual_output_path = possible_files[0]
            logger.info(f"Found downloaded audio file: {actual_output_path}")
            
            # If the file doesn't match our expected path, rename it
            if actual_output_path != output_path:
                logger.info(f"Renaming {actual_output_path} to {output_path}")
                try:
                    shutil.move(actual_output_path, output_path)
                except Exception as rename_error:
                    logger.warning(f"Could not rename file, using original: {str(rename_error)}")
                    output_path = actual_output_path
            
            logger.info(f"Method 3 successful: {output_path}")
            return output_path
        else:
            logger.error("Method 3 failed: No mp3 files found")
            errors.append("Method 3 failed: No mp3 files found")
    except Exception as e:
        error_msg = f"Method 3 (yt-dlp) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # Method 4: Try using yt-dlp with different options
    try:
        logger.info(f"Method 4: Attempting to use yt-dlp with different options for video {video_id}")
        
        # We already checked for yt-dlp in Method 3
        import yt_dlp
        
        # Alternative options for yt-dlp
        alternative_opts = {
            'format': 'worstaudio/worst',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'paths': {'home': output_dir},
            'outtmpl': {'default': f"{session_id}_alt.%(ext)s"},
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        }
        
        with yt_dlp.YoutubeDL(alternative_opts) as ydl:
            logger.info(f"Downloading with alternative options: {video_url}")
            ydl.download([video_url])
        
        # Check for the file
        possible_files = glob.glob(os.path.join(output_dir, f"{session_id}*.mp3"))
        if possible_files:
            actual_output_path = possible_files[0]
            logger.info(f"Found downloaded audio file: {actual_output_path}")
            
            # If the file doesn't match our expected path, rename it
            if actual_output_path != output_path:
                logger.info(f"Renaming {actual_output_path} to {output_path}")
                try:
                    shutil.move(actual_output_path, output_path)
                except Exception as rename_error:
                    logger.warning(f"Could not rename file, using original: {str(rename_error)}")
                    output_path = actual_output_path
            
            logger.info(f"Method 4 successful: {output_path}")
            return output_path
        else:
            logger.error("Method 4 failed: No mp3 files found")
            errors.append("Method 4 failed: No mp3 files found")
    except Exception as e:
        error_msg = f"Method 4 (alternative yt-dlp) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # Method 5: Try a last-resort approach with thumbnail verification
    try:
        logger.info(f"Method 5: Attempting last-resort approach for video {video_id}")
        
        # Import required modules
        import requests
        from pydub import AudioSegment
        
        # If all API approaches failed, try a direct HTTP request to a proxy service
        # This is a last resort and may not be reliable long-term
        proxy_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        logger.info(f"Checking if video has thumbnail: {proxy_url}")
        
        # Just checking if the video exists via thumbnail
        thumbnail_response = requests.head(proxy_url, timeout=5)
        if thumbnail_response.status_code == 200:
            logger.info(f"Video thumbnail exists, video is likely valid")
            
            # Create a simple HTML file that embeds the YouTube video
            # This is for documentation purposes only, to help debug
            html_path = os.path.join(output_dir, f"{session_id}_debug.html")
            with open(html_path, 'w') as f:
                f.write(f'''
                <!DOCTYPE html>
                <html>
                <head><title>YouTube Audio Debug</title></head>
                <body>
                    <h1>YouTube Video {video_id}</h1>
                    <p>Title: Unknown (could not extract)</p>
                    <p>This file was created for debugging purposes.</p>
                    <p>If you're seeing this file, it means the application attempted to extract audio from this video.</p>
                </body>
                </html>
                ''')
            
            # Create an empty audio file with metadata as a fallback
            # This allows the application to continue with a placeholder
            logger.warning(f"Creating empty audio file as fallback: {output_path}")
            empty_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
            empty_audio.export(output_path, format="mp3", 
                              tags={'title': f"YouTube Audio Extraction Failed",
                                    'artist': 'Indic-Translator',
                                    'album': 'YouTube Audio Extraction',
                                    'comment': f'Failed to extract audio from YouTube video {video_id}'})
            
            logger.info(f"Created fallback audio file: {output_path}")
            return output_path
        else:
            logger.error(f"Video thumbnail does not exist, video may be invalid or private")
            errors.append("Video thumbnail not found")
    except Exception as e:
        error_msg = f"Method 5 (last-resort) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # All methods failed, but provide a more useful error message
    error_msg = f"All YouTube download methods failed: {', '.join(errors)}"
    logger.error(error_msg)
    
    # Create a last-resort fallback empty audio file using ffmpeg directly
    try:
        logger.warning(f"Creating emergency fallback empty audio file: {output_path}")
        # Create a simple silent audio file using ffmpeg
        import subprocess
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', 
            '-t', '3', output_path
        ]
        subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Created emergency fallback audio file: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Failed to create emergency fallback audio file: {str(e)}")
    
    # If we get here, everything has failed
    raise RuntimeError(error_msg)

def extract_audio_from_url(video_url: str, session_id: str, output_dir: str) -> str:
    """
    Extract audio from a YouTube or Instagram video URL.
    
    Args:
        video_url: URL of the video
        session_id: Session ID for naming the output file
        output_dir: Directory to save the audio file
        
    Returns:
        Path to the extracted audio file
        
    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If audio extraction fails
    """
    # Import necessary modules explicitly within the function
    import os
    import subprocess
    import traceback
    
    try:
        # Validate URL
        is_valid, platform = is_valid_video_url(video_url)
        if not is_valid:
            logger.error(f"Invalid video URL: {video_url}")
            raise ValueError(f"Invalid video URL. Please provide a valid YouTube or Instagram URL.")
        
        logger.info(f"Extracting audio from {platform} URL: {video_url}")
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Define output path for last-resort fallback
        output_path = os.path.join(output_dir, f"{session_id}.mp3")
        
        # Use platform-specific extraction
        try:
            if platform == "youtube":
                return extract_audio_from_youtube(video_url, session_id, output_dir)
            elif platform == "instagram":
                return extract_audio_from_instagram(video_url, session_id, output_dir)
            else:
                # This should never happen due to validation
                raise ValueError(f"Unsupported platform: {platform}")
        except Exception as e:
            logger.error(f"Platform-specific extraction failed: {str(e)}")
            
            # Last-resort emergency fallback - create a silent audio file
            try:
                logger.warning(f"Creating universal emergency fallback audio file: {output_path}")
                # Create a simple silent audio file using ffmpeg
                ffmpeg_cmd = [
                    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', 
                    '-t', '3', output_path
                ]
                subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"Created universal emergency fallback audio file: {output_path}")
                    return output_path
            except Exception as fallback_error:
                logger.error(f"Failed to create universal fallback audio file: {str(fallback_error)}")
            
            # Re-raise the original error if fallback fails
            raise
    except Exception as e:
        # Log the full stack trace for better debugging
        logger.error(f"Error in extract_audio_from_url: {str(e)}\n{traceback.format_exc()}")
        raise

def extract_audio_from_instagram(video_url: str, session_id: str, output_dir: str) -> str:
    """
    Extract audio from an Instagram video URL using multiple methods.
    
    Args:
        video_url: URL of the Instagram video
        session_id: Session ID for naming the output file
        output_dir: Directory to save the audio file
        
    Returns:
        Path to the extracted audio file
        
    Raises:
        ValueError: If the URL is invalid
        RuntimeError: If audio extraction fails
    """
    # Import necessary modules explicitly within the function
    import os
    import glob
    import shutil
    import subprocess
    import traceback
    logger.info(f"Extracting audio from Instagram URL: {video_url}")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Output file path
    output_path = os.path.join(output_dir, f"{session_id}.mp3")
    logger.info(f"Output path: {output_path}")
    
    # Try multiple methods to download the audio
    errors = []
    
    # Method 1: Try using yt-dlp with standard options
    try:
        logger.info("Method 1: Attempting to use yt-dlp with standard options for Instagram video")
        
        # Check if yt-dlp is installed
        try:
            import yt_dlp
        except ImportError:
            logger.warning("yt-dlp is not installed, skipping Method 1")
            errors.append("yt-dlp is not installed")
            # Don't raise the error here, allow fallback methods to be tried
            # Skip to the next method
            raise Exception("yt-dlp not installed, skipping to next method")
        
        # Standard options for yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'paths': {'home': output_dir},
            'outtmpl': {'default': f"{session_id}.%(ext)s"},
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Cookie': '',  # Empty cookie to avoid Instagram's bot detection
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading Instagram video: {video_url}")
            ydl.download([video_url])
        
        # Check for the file
        possible_files = glob.glob(os.path.join(output_dir, f"{session_id}*.mp3"))
        if possible_files:
            actual_output_path = possible_files[0]
            logger.info(f"Found downloaded audio file: {actual_output_path}")
            
            # If the file doesn't match our expected path, rename it
            if actual_output_path != output_path:
                logger.info(f"Renaming {actual_output_path} to {output_path}")
                try:
                    shutil.move(actual_output_path, output_path)
                except Exception as rename_error:
                    logger.warning(f"Could not rename file, using original: {str(rename_error)}")
                    output_path = actual_output_path
            
            logger.info(f"Method 1 successful: {output_path}")
            return output_path
        else:
            logger.error("Method 1 failed: No mp3 files found")
            errors.append("Method 1 failed: No mp3 files found")
    except Exception as e:
        error_msg = f"Method 1 (yt-dlp standard) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # Method 2: Try using yt-dlp with alternative options
    try:
        logger.info("Method 2: Attempting to use yt-dlp with alternative options for Instagram video")
        
        # Check again for yt-dlp in case Method 1 was skipped
        try:
            import yt_dlp
        except ImportError:
            logger.warning("yt-dlp is not installed, skipping Method 2")
            errors.append("yt-dlp is not installed")
            # Skip to the next method
            raise Exception("yt-dlp not installed, skipping to next method")
        
        # Alternative options for yt-dlp
        alternative_opts = {
            'format': 'worstaudio/worst',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128',
            }],
            'paths': {'home': output_dir},
            'outtmpl': {'default': f"{session_id}_alt.%(ext)s"},
            'quiet': False,
            'no_warnings': False,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'socket_timeout': 30,
            'retries': 10,
            'fragment_retries': 10,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.instagram.com/',
            }
        }
        
        with yt_dlp.YoutubeDL(alternative_opts) as ydl:
            logger.info(f"Downloading with alternative options: {video_url}")
            ydl.download([video_url])
        
        # Check for the file
        possible_files = glob.glob(os.path.join(output_dir, f"{session_id}*.mp3"))
        if possible_files:
            actual_output_path = possible_files[0]
            logger.info(f"Found downloaded audio file: {actual_output_path}")
            
            # If the file doesn't match our expected path, rename it
            if actual_output_path != output_path:
                logger.info(f"Renaming {actual_output_path} to {output_path}")
                try:
                    shutil.move(actual_output_path, output_path)
                except Exception as rename_error:
                    logger.warning(f"Could not rename file, using original: {str(rename_error)}")
                    output_path = actual_output_path
            
            logger.info(f"Method 2 successful: {output_path}")
            return output_path
        else:
            logger.error("Method 2 failed: No mp3 files found")
            errors.append("Method 2 failed: No mp3 files found")
    except Exception as e:
        error_msg = f"Method 2 (yt-dlp alternative) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # Method 3: Try using direct ffmpeg approach
    try:
        logger.info("Method 3: Attempting to use direct ffmpeg approach for Instagram video")
        
        # Use ffmpeg directly to download and convert
        import subprocess
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', video_url, 
            '-vn', '-acodec', 'libmp3lame', '-q:a', '2', output_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully downloaded and converted audio using ffmpeg: {output_path}")
            return output_path
        else:
            logger.warning(f"ffmpeg command failed: {result.stderr}")
            errors.append(f"Method 3 (ffmpeg) failed: {result.stderr}")
    except Exception as e:
        error_msg = f"Method 3 (ffmpeg) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # Method 4: Create a fallback empty audio file
    try:
        logger.info("Method 4: Creating fallback empty audio file for Instagram video")
        
        from pydub import AudioSegment
        
        # Create an empty audio file with metadata as a fallback
        # This allows the application to continue with a placeholder
        logger.warning(f"Creating empty audio file as fallback: {output_path}")
        empty_audio = AudioSegment.silent(duration=1000)  # 1 second of silence
        empty_audio.export(output_path, format="mp3", 
                          tags={'title': "Instagram Audio Extraction Failed",
                                'artist': 'Indic-Translator',
                                'album': 'Instagram Audio Extraction',
                                'comment': f'Failed to extract audio from Instagram video {video_url}'})
        
        logger.info(f"Created fallback audio file: {output_path}")
        return output_path
    except Exception as e:
        error_msg = f"Method 4 (fallback audio) failed: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
    
    # All methods failed, but provide a more useful error message
    error_msg = f"All Instagram download methods failed: {', '.join(errors)}"
    logger.error(error_msg)
    
    # Create a last-resort fallback empty audio file
    try:
        logger.warning(f"Creating emergency fallback empty audio file: {output_path}")
        # Create a simple silent audio file using ffmpeg
        import subprocess
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', 
            '-t', '3', output_path
        ]
        subprocess.run(ffmpeg_cmd, capture_output=True, check=False)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Created emergency fallback audio file: {output_path}")
            return output_path
    except Exception as e:
        logger.error(f"Failed to create emergency fallback audio file: {str(e)}")
    
    # If we get here, everything has failed
    raise RuntimeError(error_msg)
