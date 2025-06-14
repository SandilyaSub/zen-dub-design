import os
import logging
import sys
from dotenv import load_dotenv
from modules.sarvam_tts import synthesize_speech

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_sarvam_tts():
    """
    Test the Sarvam TTS API with Telugu text.
    """
    # Telugu text to synthesize
    telugu_text = """మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము.....మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము....మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము.....మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము.....మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము....మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము..."""
    
    # Output path
    output_path = "test_sarvam_tts_output.mp3"
    
    # Check if Sarvam API key exists
    sarvam_api_key = os.environ.get('SARVAM_API_KEY')
    if not sarvam_api_key:
        logger.error("No Sarvam API key found in environment variables.")
        print("❌ Sarvam TTS API test failed: No API key found!")
        return False
    
    logger.info(f"Sarvam API key available: {'Yes' if sarvam_api_key else 'No'}")
    
    # Test parameters
    language = "telugu"
    speaker = "anushka"  # Use a compatible speaker for bulbul:v2 model
    
    logger.info(f"Testing Sarvam TTS with text: {telugu_text[:50]}...")
    logger.info(f"Language: {language}, Speaker: {speaker}")
    
    # Call the synthesize_speech function
    success = synthesize_speech(
        text=telugu_text,
        language=language,
        output_path=output_path,
        speaker=speaker,
        pitch=0,
        pace=1.0,
        loudness=1.0
    )
    
    if success:
        logger.info(f"Successfully synthesized speech to: {output_path}")
        return True
    else:
        logger.error("Failed to synthesize speech")
        return False

if __name__ == "__main__":
    # Test the Sarvam TTS API
    success = test_sarvam_tts()
    
    if success:
        print("✅ Sarvam TTS API test successful!")
    else:
        print("❌ Sarvam TTS API test failed!")
        sys.exit(1)
