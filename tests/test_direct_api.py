import os
import json
import requests
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_direct_api(audio_path, model="saarika:v2", with_diarization=True):
    """Test direct API call to Sarvam with diarization."""
    logger.info(f"Testing direct API with file: {audio_path}")
    
    url = "https://api.sarvam.ai/speech-to-text"
    headers = {'API-Subscription-Key': SARVAM_API_KEY}
    
    with open(audio_path, 'rb') as audio_file:
        files = {'file': (os.path.basename(audio_path), audio_file, 'audio/wav')}
        data = {
            "model": model,
            "with_diarization": "true" if with_diarization else "false",
            "with_timestamps": "true"
        }
        
        logger.info(f"Making API request to: {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Data: {data}")
        
        response = requests.post(url, headers=headers, files=files, data=data)
        
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            # Save the full response to a file
            with open('direct_api_response.json', 'w') as f:
                json.dump(result, f, indent=2)
            
            logger.info("Response saved to direct_api_response.json")
            
            # Check if diarization data is present
            if "diarization" in result:
                logger.info("Diarization data is present in the response!")
                logger.info(f"Number of speakers detected: {len(result.get('diarization', []))}")
                return True
            else:
                logger.info("No diarization data found in the response.")
                return False
        else:
            logger.error(f"Error: {response.status_code} - {response.text}")
            return False

if __name__ == "__main__":
    audio_path = "/Users/sandilya/Sandy/Startup Ideas/Speech Based/Bravoventure.wav"
    has_diarization = test_direct_api(audio_path)
    
    if has_diarization:
        print("\n✅ SUCCESS: Direct API supports diarization!")
    else:
        print("\n❌ FAILURE: Direct API does not support diarization or an error occurred.")
