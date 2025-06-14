import os
import sys
from dotenv import load_dotenv
from modules.cartesia_tts import synthesize_speech

# Load environment variables
load_dotenv()

def main():
    # Hindi text to synthesize
    hindi_text = """तो हमको बहुत प्रॉब्लम हुई है। हमें यह दिक्कत हुई है कि यूलू की गाड़ी एकदम बंद हो जाती है बीच-बीच में और आप एकदम सर्विस को अच्छे नहीं कर रहे हो और प्राइस बढ़ाते जा रहे हो। बैटरी भी नहीं मिलती है, गाड़ी भी नहीं मिलती है। क्या करें? हम इसीलिए छोड़ दिए हैं।"""
    
    # Output path
    output_path = "test_cartesia_module_output.mp3"
    
    # Test the module
    success = synthesize_speech(
        text=hindi_text,
        output_path=output_path,
        voice_id="6452a836-cd72-45bc-ab0d-b47b999594dd"  # Dhwani's voice
    )
    
    if success:
        print(f"Successfully synthesized speech to: {output_path}")
    else:
        print("Failed to synthesize speech")
        sys.exit(1)

if __name__ == "__main__":
    main()
