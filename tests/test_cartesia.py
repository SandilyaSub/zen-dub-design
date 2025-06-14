import os
import logging
import requests
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cartesia API key and version from environment
CARTESIA_API_KEY = os.environ.get('CARTESIA_API_KEY')
CARTESIA_API_VERSION = os.environ.get('CARTESIA_API_VERSION', '2024-11-13')

def test_cartesia_tts(text, output_path="test_output.mp3", voice_id="6452a836-cd72-45bc-ab0d-b47b999594dd"):
    """
    Test the Cartesia TTS API with detailed error reporting.
    
    Args:
        text: Text to synthesize
        output_path: Path to save the synthesized audio
        voice_id: Voice ID to use
    """
    logger.info(f"Testing Cartesia TTS API with text: {text[:50]}...")
    
    # Check for API key
    if not CARTESIA_API_KEY:
        logger.error("No Cartesia API key found in environment variables.")
        return False
    
    logger.info(f"Using API key: {CARTESIA_API_KEY[:5]}...")
    logger.info(f"Using API version: {CARTESIA_API_VERSION}")
    
    # Prepare API request
    url = "https://api.cartesia.ai/tts/bytes"
    headers = {
        "Cartesia-Version": CARTESIA_API_VERSION,
        "X-API-Key": CARTESIA_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model_id": "sonic-2",
        "transcript": text,
        "voice": {
            "mode": "id",
            "id": voice_id
        },
        "output_format": {
            "container": "mp3",
            "bit_rate": 128000,
            "sample_rate": 44100
        },
        "language": "hi"  # Hindi is the only language we use Cartesia for
    }
    
    logger.info(f"Sending request to {url} with payload: {json.dumps(payload, indent=2)}")
    
    try:
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Log the raw response for debugging
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Check content type to determine how to handle the response
        content_type = response.headers.get('Content-Type', '')
        logger.info(f"Content-Type: {content_type}")
        
        # Check for successful response
        if response.status_code == 200:
            # If content type is audio, save directly
            if 'audio' in content_type:
                logger.info("Received audio data directly")
                
                try:
                    # Save the audio data
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    
                    logger.info(f"Speech synthesis complete: {output_path}")
                    return True
                except Exception as e:
                    logger.error(f"Error saving audio data: {e}")
                    return False
            else:
                # Try to parse as JSON (old approach)
                try:
                    result = response.json()
                    logger.info("Successfully parsed JSON response")
                    
                    # Extract audio data
                    audio_base64 = result.get("audio", "")
                    if audio_base64:
                        try:
                            audio_data = base64.b64decode(audio_base64)
                            
                            # Save the audio data
                            with open(output_path, "wb") as f:
                                f.write(audio_data)
                            
                            logger.info(f"Speech synthesis complete: {output_path}")
                            return True
                        except Exception as e:
                            logger.error(f"Error decoding or saving audio data: {e}")
                            return False
                    else:
                        logger.error("No audio data received from API")
                        return False
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    return False
        else:
            logger.error(f"API request failed with status code {response.status_code}")
            try:
                error_json = response.json()
                logger.error(f"Error details: {json.dumps(error_json, indent=2)}")
            except:
                logger.error(f"Error details (raw): {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"Exception during API request: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Hindi text to synthesize
    hindi_text = """तो हमको बहुत प्रॉब्लम हुई है। हमें यह दिक्कत हुई है कि यूलू की गाड़ी एकदम बंद हो जाती है बीच-बीच में और आप एकदम सर्विस को अच्छे नहीं कर रहे हो और प्राइस बढ़ाते जा रहे हो। बैटरी भी नहीं मिलती है, गाड़ी भी नहीं मिलती है। क्या करें? हम इसीलिए छोड़ दिए हैं।"""
    
    # Test the API
    test_cartesia_tts(hindi_text)
