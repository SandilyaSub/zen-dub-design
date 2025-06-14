import os
import logging
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cartesia_direct():
    """
    Test the Cartesia TTS API directly with hard-coded API key and version.
    """
    # Hindi text to synthesize
    hindi_text = """पिताजी ने समय देखकर फ़ोन उठाया क्या आप, पंडित जी, निकलने वाले हैं? आधे घंटे में राहु काल समाप्त हो जाएगा। जैसे ही हो सके निकल जाइए मेरे बेटे की जन्म कुंडली आपने ही लिखी थी। क्या सिर्फ़ वो ले जाने से ही काम चल जाएगा? और कुछ ले जाने की आवश्यकता है? मेरे बेटे की कुंडली के साथ, मेरे बेटे को भी ले जाएं। बेटा क्यों पंडित जी? अगर वह अपनी कुंडली सुनेगा तो उत्तेजित हो जाएगा, और नहीं सुनेगा तो निराश हो जाएगा। मुझे कुंडली में कुछ दिखाई नहीं दे रहा। क्या उसकी हथेली देखनी चाहिए? उसकी हथेली में कुछ दिखाई नहीं दे रहा। क्या उसके पैर देखने चाहिए? क्या उसके पैरों में भी कुछ नहीं दिखाई दे रहा? क्या आपको समझ आया? आप उस व्यक्ति से मिलना चाहते हैं? मैं उसे ले आता हूँ। सभी फ़ोन रख देंगे। क्या?"""
    
    # Output path
    output_path = "test_cartesia_direct_output.mp3"
    
    # Get API key from environment
    api_key = os.environ.get('CARTESIA_API_KEY')
    api_version = os.environ.get('CARTESIA_API_VERSION', '2024-11-13')
    
    logger.info(f"API Key available: {'Yes' if api_key else 'No'}")
    logger.info(f"API Version: {api_version}")
    
    # If no API key, try to use a hardcoded one for testing
    if not api_key:
        logger.warning("No API key found in environment. Please set CARTESIA_API_KEY in your .env file.")
        return False
    
    # Prepare API request
    url = "https://api.cartesia.ai/tts/bytes"
    headers = {
        "Cartesia-Version": api_version,
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "model_id": "sonic-2",
        "transcript": hindi_text,
        "voice": {
            "mode": "id",
            "id": "6452a836-cd72-45bc-ab0d-b47b999594dd"  # Dhwani's voice
        },
        "output_format": {
            "container": "mp3",
            "bit_rate": 128000,
            "sample_rate": 44100
        },
        "language": "hi"  # Hindi language
    }
    
    logger.info(f"Sending request to {url}")
    
    try:
        # Make API request
        response = requests.post(url, headers=headers, json=payload)
        
        # Log the response status
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Check for successful response
        if response.status_code == 200:
            # Save the audio data
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            logger.info(f"Speech synthesis complete: {output_path}")
            return True
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
    # Test the API
    success = test_cartesia_direct()
    
    if success:
        print("✅ Cartesia TTS API test successful!")
    else:
        print("❌ Cartesia TTS API test failed!")
