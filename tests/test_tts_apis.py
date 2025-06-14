import os
import logging
import sys
from dotenv import load_dotenv
from modules.cartesia_tts import synthesize_speech as cartesia_synthesize
from modules.sarvam_tts import synthesize_speech as sarvam_synthesize

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tts_apis():
    """
    Test both Cartesia and Sarvam TTS APIs with the provided texts.
    """
    # Test texts
    hindi_text = """तो हमको बहुत प्रॉब्लम हुई है। हमें यह दिक्कत हुई है कि यूलू की गाड़ी एकदम बंद हो जाती है बीच-बीच में और आप एकदम सर्विस को अच्छे नहीं कर रहे हो और प्राइस बढ़ाते जा रहे हो। बैटरी भी नहीं मिलती है, गाड़ी भी नहीं मिलती है। क्या करें? हम इसीलिए छोड़ दिए हैं।"""
    
    telugu_text = """మాకు చాలా ఇబ్బందిగా ఉంది.. యులు బైక్‌లో సమస్య ఎదురవుతోంది.. ఇది ప్రయాణ మధ్యలో ఆగిపోతుంది, కాబట్టి మాకు మంచి సేవ లభించదు.. ధర పెరుగుతూనే ఉంది, బ్యాటరీ కూడా దొరకడం లేదు, బైక్ కూడా దొరకడం లేదు.. మనం ఏమి చేయగలం? అందుకే వదులుకున్నాము."""
    
    # Output paths
    cartesia_output_path = "test_cartesia_final_output.mp3"
    sarvam_output_path = "test_sarvam_final_output.mp3"
    
    # Check API keys
    cartesia_api_key = os.environ.get('CARTESIA_API_KEY')
    sarvam_api_key = os.environ.get('SARVAM_API_KEY')
    
    logger.info(f"Cartesia API key available: {'Yes' if cartesia_api_key else 'No'}")
    logger.info(f"Sarvam API key available: {'Yes' if sarvam_api_key else 'No'}")
    
    # Test results
    cartesia_success = False
    sarvam_success = False
    
    # Test Cartesia TTS with Hindi text
    logger.info("Testing Cartesia TTS with Hindi text...")
    cartesia_success = cartesia_synthesize(
        text=hindi_text,
        output_path=cartesia_output_path,
        voice_id="6452a836-cd72-45bc-ab0d-b47b999594dd"  # Dhwani's voice
    )
    
    if cartesia_success:
        logger.info(f"Cartesia TTS test successful. Output saved to: {cartesia_output_path}")
    else:
        logger.error("Cartesia TTS test failed.")
    
    # Test Sarvam TTS with Telugu text
    logger.info("Testing Sarvam TTS with Telugu text...")
    sarvam_success = sarvam_synthesize(
        text=telugu_text,
        language="telugu",
        output_path=sarvam_output_path,
        speaker="anushka",  # Compatible with bulbul:v2
        model="bulbul:v2"
    )
    
    if sarvam_success:
        logger.info(f"Sarvam TTS test successful. Output saved to: {sarvam_output_path}")
    else:
        logger.error("Sarvam TTS test failed.")
    
    return cartesia_success, sarvam_success

if __name__ == "__main__":
    # Test both TTS APIs
    cartesia_success, sarvam_success = test_tts_apis()
    
    if cartesia_success and sarvam_success:
        print("✅ Both TTS API tests successful!")
    elif cartesia_success:
        print("✅ Cartesia TTS API test successful!")
        print("❌ Sarvam TTS API test failed!")
        sys.exit(1)
    elif sarvam_success:
        print("❌ Cartesia TTS API test failed!")
        print("✅ Sarvam TTS API test successful!")
        sys.exit(1)
    else:
        print("❌ Both TTS API tests failed!")
        sys.exit(1)
