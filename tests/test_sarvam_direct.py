import os
import logging
import sys
import requests
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Language code mapping
LANGUAGE_MAP = {
    'hindi': 'hi-IN',
    'english': 'en-IN',
    'telugu': 'te-IN',
    'tamil': 'ta-IN',
    'kannada': 'kn-IN',
    'gujarati': 'gu-IN',
    'marathi': 'mr-IN',
    'bengali': 'bn-IN',
    'odia': 'od-IN',
    'punjabi': 'pa-IN',
    'malayalam': 'ml-IN'
}

# Available speakers for bulbul:v2 model
BULBUL_SPEAKERS = ["anushka", "abhilash", "manisha", "vidya", "arya", "karun", "hitesh"]

def test_sarvam_direct():
    """
    Test the Sarvam TTS API directly with the API key from environment.
    """
    # Telugu text to synthesize
    telugu_text = """మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము."""
    
    # Output path
    output_path = "test_sarvam_direct_output.mp3"
    
    # Get API key from environment
    api_key = os.environ.get('SARVAM_API_KEY')
    if not api_key:
        logger.error("No Sarvam API key found in environment variables.")
        return False
    
    logger.info(f"API Key available: {'Yes' if api_key else 'No'}")
    logger.info(f"API Key: {api_key[:5]}...")
    
    # Test parameters
    language = "telugu"
    language_code = LANGUAGE_MAP.get(language, language)
    speaker = "anushka"  # Using a speaker compatible with bulbul:v2
    
    logger.info(f"Testing Sarvam TTS with text: {telugu_text[:50]}...")
    logger.info(f"Language: {language} ({language_code}), Speaker: {speaker}")
    
    # Prepare API request
    url = "https://api.sarvam.ai/text-to-speech"
    headers = {
        "API-Subscription-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Ensure text is not too long (Sarvam has a 500 character limit per input)
    # Split into chunks if necessary
    text_chunks = []
    max_chunk_size = 500
    
    if len(telugu_text) <= max_chunk_size:
        text_chunks = [telugu_text]
    else:
        # Split by sentences to avoid cutting in the middle of a sentence
        sentences = telugu_text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            # Add period back if it was removed during split
            if not sentence.endswith('.'):
                sentence += '.'
            
            # If adding this sentence would exceed the limit, start a new chunk
            if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                text_chunks.append(current_chunk)
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += ' ' + sentence
                else:
                    current_chunk = sentence
        
        # Add the last chunk if it's not empty
        if current_chunk:
            text_chunks.append(current_chunk)
    
    logger.info(f"Split text into {len(text_chunks)} chunks")
    
    try:
        # Process each chunk
        all_audio_data = bytearray()
        
        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processing chunk {i+1}/{len(text_chunks)}")
            
            payload = {
                "inputs": [chunk],
                "target_language_code": language_code,
                "speaker": speaker,
                "pitch": 0,
                "pace": 1.0,
                "loudness": 1.0,
                "speech_sample_rate": 22050,  # Highest quality
                "enable_preprocessing": True,
                "model": "bulbul:v2"  # Latest model
            }
            
            logger.info(f"Sending request to {url} with payload: {json.dumps(payload, indent=2)}")
            
            # Make API request
            response = requests.post(url, headers=headers, json=payload)
            
            # Log the response status
            logger.info(f"Response status code: {response.status_code}")
            
            # Check for successful response
            if response.status_code == 200:
                result = response.json()
                
                # Extract audio data
                audio_base64 = result.get("audios", [""])[0]
                if audio_base64:
                    audio_data = base64.b64decode(audio_base64)
                    all_audio_data.extend(audio_data)
                    logger.info(f"Received audio data for chunk {i+1}")
                else:
                    logger.error("No audio data received from API")
                    return False
            else:
                logger.error(f"API request failed with status code {response.status_code}")
                try:
                    error_json = response.json()
                    logger.error(f"Error details: {json.dumps(error_json, indent=2)}")
                except:
                    logger.error(f"Error details (raw): {response.text}")
                return False
        
        # Save the combined audio data
        with open(output_path, "wb") as f:
            f.write(all_audio_data)
        
        logger.info(f"Speech synthesis complete: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Exception during API request: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Test the API
    success = test_sarvam_direct()
    
    if success:
        print("✅ Sarvam TTS API test successful!")
    else:
        print("❌ Sarvam TTS API test failed!")
        sys.exit(1)
