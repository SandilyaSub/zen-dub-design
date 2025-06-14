#!/usr/bin/env python3
"""
Sarvam Chat Completions API Translation Test Script
==================================================

OBJECTIVE:
This script evaluates the quality of translations performed by Sarvam's new Chat Completions API
with the Sarvam-m model. It takes a diarization JSON file, translates it to a target language,
back-translates it to the original language, and calculates quality metrics.

USAGE:
    python test_sarvam_translation.py --input_file <path> --source_language <lang> --target_language <lang> --api_key <key>

ARGUMENTS:
    --input_file      : Path to input diarization.json file (required)
    --source_language : Source language of the content (required)
    --target_language : Target language for translation (required)
    --api_key         : Sarvam API key (required if not set in environment)
    --output_dir      : Directory to save output files (default: tests/output)

EXAMPLE:
    python test_sarvam_translation.py \
        --input_file /path/to/diarization.json \
        --source_language english \
        --target_language hindi \
        --api_key sk_sar_YOUR_API_KEY

OUTPUT:
    The script generates three files in the output directory:
    1. <filename>_sarvam_translated_<timestamp>.json - The translated content
    2. <filename>_sarvam_back_translated_<timestamp>.json - The back-translated content
    3. <filename>_sarvam_metrics_<timestamp>.json - Quality metrics (BERT, BLEU, etc.)

NOTES:
    - The input file must be in the standard diarization.json format with "segments" array
    - Each segment should have a "text" field containing the content to translate
    - The output follows the same format with added "translated_text" fields
"""

import os
import sys
import json
import argparse
import datetime
import logging
from pathlib import Path
import copy

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Sarvam translation module
from modules.sarvam_translation import (
    translate_diarized_content,
    translate_text,
    get_sarvam_api_key
)

# Import metrics calculation from existing module
from modules.translation_metrics import (
    calculate_bert_scores,
    calculate_bleu_scores,
    compute_enhanced_composite_metric,
    normalize_language_code
)

# Configure logging
os.makedirs("tests/output", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"tests/output/sarvam_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Test Sarvam Chat Completions API for translation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 test_sarvam_translation.py --input_file data/diarization.json --source_language english --target_language hindi --api_key sk_sar_YOUR_API_KEY
  python3 test_sarvam_translation.py --input_file data/diarization.json --source_language english --target_language telugu --output_dir custom_output
        """
    )
    parser.add_argument('--input_file', required=True, help='Path to input diarization.json file')
    parser.add_argument('--source_language', required=True, help='Source language (e.g., english, hindi)')
    parser.add_argument('--target_language', required=True, help='Target language (e.g., english, hindi)')
    parser.add_argument('--output_dir', default='tests/output', help='Output directory')
    parser.add_argument('--api_key', required=True, help='Sarvam API key')
    return parser.parse_args()

def calculate_english_word_preservation(original_data, translated_data):
    """
    Calculate the percentage of English words preserved in translation.
    
    Args:
        original_data: Original diarization data
        translated_data: Translated diarization data
        
    Returns:
        Percentage of English words preserved
    """
    import re
    
    # Extract English words (simple approach - words with only Latin characters)
    english_pattern = re.compile(r'\b[a-zA-Z]+\b')
    
    # Get all segments
    original_segments = original_data.get("segments", [])
    translated_segments = translated_data.get("segments", [])
    
    if len(original_segments) != len(translated_segments):
        logger.error(f"Segment count mismatch: {len(original_segments)} vs {len(translated_segments)}")
        return 0.0
    
    total_english_words = 0
    preserved_words = 0
    
    for i, (orig_seg, trans_seg) in enumerate(zip(original_segments, translated_segments)):
        orig_text = orig_seg.get("text", "")
        trans_text = trans_seg.get("text", "")
        
        # Find English words in original text
        original_english_words = set(english_pattern.findall(orig_text))
        total_english_words += len(original_english_words)
        
        # Count preserved words
        if original_english_words:
            for word in original_english_words:
                if word in trans_text:
                    preserved_words += 1
    
    # Calculate preservation rate
    if total_english_words > 0:
        preservation_rate = (preserved_words / total_english_words) * 100
    else:
        preservation_rate = 100.0  # No English words to preserve
    
    return preservation_rate

def calculate_metrics(original_data, back_translated_data, translated_data=None):
    """
    Calculate BERT, BLEU scores, and English word preservation between original and back-translated text.
    
    Args:
        original_data: Original diarization data
        back_translated_data: Back-translated diarization data
        translated_data: Translated diarization data (for English word preservation)
        
    Returns:
        Dictionary of metrics
    """
    try:
        # Calculate BERT scores
        bert_scores = calculate_bert_scores(original_data, back_translated_data)
        
        # Calculate BLEU scores
        bleu_scores = calculate_bleu_scores(original_data, back_translated_data)
        
        # Calculate English word preservation if translated data is provided
        english_preservation = 0.0
        if translated_data:
            english_preservation = calculate_english_word_preservation(original_data, translated_data)
            logger.info(f"English word preservation: {english_preservation:.2f}%")
        
        # Combine metrics
        metrics = {
            "bert_scores": bert_scores,
            "bleu_scores": bleu_scores,
            "english_preservation": english_preservation,
            "overall": {
                "bert_score": bert_scores.get("bert_overall", 0.0) * 100,  # Convert to percentage
                "bleu_score": bleu_scores.get("bleu_overall", 0.0),
                "english_preservation": english_preservation
            }
        }
        
        # Calculate composite score
        metrics["overall"]["composite_score"] = (
            0.4 * metrics["overall"]["bert_score"] +
            0.3 * metrics["overall"]["bleu_score"] +
            0.3 * metrics["overall"]["english_preservation"]
        )
        
        return metrics
    
    except ImportError as e:
        logger.error(f"Required package not found: {e}")
        logger.error("Please ensure all required packages are installed")
        return {"error": f"Required package not found: {e}"}
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": f"Error calculating metrics: {e}"}

def main():
    """Main function to run the test."""
    args = parse_arguments()
    
    # Set API key if provided
    if args.api_key:
        os.environ['SARVAM_API_KEY'] = args.api_key
        logger.info("Using API key from command line arguments")
    
    # Validate input file
    input_file = Path(args.input_file)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for output files
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    base_filename = input_file.stem
    
    # Load input diarization data
    logger.info(f"Loading diarization data from {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            diarization_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading input file: {e}")
        sys.exit(1)
    
    # Translate diarization data
    logger.info(f"Translating from {args.source_language} to {args.target_language}")
    try:
        translated_data = translate_diarized_content(
            diarization_data,
            args.target_language,
            args.source_language,
            api_key=args.api_key
        )
        
        # Fix naming conventions in translated data
        logger.info("Fixing naming conventions in translated data")
        
        # Create a new structure with the correct naming conventions
        fixed_translated_data = {
            "transcript": diarization_data.get("transcript", ""),
            "segments": [],
            "language_code": diarization_data.get("language_code", ""),
            "translation_info": translated_data.get("metadata", {}).get("translation", {})
        }
        
        # Create translated_transcript from all translated segments
        translated_transcript = " ".join([s.get("text", "") for s in translated_data.get("segments", [])])
        fixed_translated_data["translated_transcript"] = translated_transcript
        
        # Update segment fields
        for i, segment in enumerate(translated_data.get("segments", [])):
            if i < len(diarization_data.get("segments", [])):
                # Create a new segment with correct fields
                new_segment = {
                    "segment_id": segment.get("segment_id", ""),
                    "speaker": segment.get("speaker", ""),
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "gender": segment.get("gender", "unknown"),
                    "pace": segment.get("pace", 1.0),
                    "text": diarization_data["segments"][i].get("text", ""),
                    "translated_text": segment.get("text", "")
                }
                fixed_translated_data["segments"].append(new_segment)
        
        # Replace translated_data with fixed_translated_data
        translated_data = fixed_translated_data
    except Exception as e:
        logger.error(f"Error translating diarization data: {e}")
        sys.exit(1)
    
    # Save translated data
    translated_file = output_dir / f"{base_filename}_sarvam_translated_{timestamp}.json"
    logger.info(f"Saving translated data to {translated_file}")
    with open(translated_file, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    
    # Back-translate segments
    logger.info(f"Back-translating from {args.target_language} to {args.source_language}")
    try:
        # First, create a copy of translated data to use for back-translation
        # This is important because we need to preserve the original translated_text values
        back_translation_input = copy.deepcopy(translated_data)
        
        # For back-translation, we need to use the translated text as input
        for segment in back_translation_input.get("segments", []):
            if "translated_text" in segment and segment["translated_text"]:
                # Move translated_text to text for the back-translation process
                segment["text"] = segment["translated_text"]
        
        # Perform back-translation
        back_translated_data_raw = translate_diarized_content(
            back_translation_input,
            args.source_language,
            args.target_language,
            api_key=args.api_key
        )
        
        # Fix the structure of back-translated data to match what metrics module expects
        logger.info("Fixing back-translated data structure for metrics calculation")
        
        # Create a new structure with the correct naming conventions
        back_translated_data = {
            "transcript": diarization_data.get("transcript", ""),
            "segments": [],
            "language_code": diarization_data.get("language_code", ""),
            "translation_info": back_translated_data_raw.get("metadata", {}).get("translation", {})
        }
        
        # Add translated_transcript field from the translated data
        back_translated_data["translated_transcript"] = translated_data.get("translated_transcript", "")
        
        # Process each segment
        for i, segment in enumerate(back_translated_data_raw.get("segments", [])):
            if i < len(diarization_data.get("segments", [])) and i < len(translated_data.get("segments", [])):
                # Get original text from diarization_data
                original_text = diarization_data["segments"][i].get("text", "")
                
                # Get translated text from translated_data
                translated_text = translated_data["segments"][i].get("translated_text", "")
                
                # Get back-translated text from the raw back-translation
                back_translated_text = segment.get("text", "")
                
                # Create a new segment with correct fields
                new_segment = {
                    "segment_id": segment.get("segment_id", ""),
                    "speaker": segment.get("speaker", ""),
                    "start_time": segment.get("start_time", 0),
                    "end_time": segment.get("end_time", 0),
                    "gender": segment.get("gender", "unknown"),
                    "pace": segment.get("pace", 1.0),
                    "text": original_text,
                    "translated_text": translated_text,
                    "back_translated_text": back_translated_text
                }
                back_translated_data["segments"].append(new_segment)
        
        # Add back_translation field (full back-translated text)
        back_translation = " ".join([s.get("back_translated_text", "") for s in back_translated_data.get("segments", [])])
        back_translated_data["back_translation"] = back_translation
        
        # Add back_translated_transcript field for metrics calculation
        back_translated_data["back_translated_transcript"] = back_translation
    except Exception as e:
        logger.error(f"Error back-translating data: {e}")
        sys.exit(1)
    
    # Save back-translated data
    back_translated_file = output_dir / f"{base_filename}_sarvam_back_translated_{timestamp}.json"
    logger.info(f"Saving back-translated data to {back_translated_file}")
    with open(back_translated_file, 'w', encoding='utf-8') as f:
        json.dump(back_translated_data, f, ensure_ascii=False, indent=2)
    
    # Calculate metrics
    logger.info("Calculating translation metrics")
    try:
        metrics = calculate_metrics(diarization_data, back_translated_data, translated_data)
        
        # Save metrics
        metrics_file = output_dir / f"{base_filename}_sarvam_metrics_{timestamp}.json"
        logger.info(f"Saving metrics to {metrics_file}")
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
        
        # Print summary
        logger.info("Translation evaluation complete")
        logger.info(f"BERT Score: {metrics.get('overall', {}).get('bert_score', 0):.2f}%")
        logger.info(f"BLEU Score: {metrics.get('overall', {}).get('bleu_score', 0):.2f}%")
        logger.info(f"English Preservation: {metrics.get('overall', {}).get('english_preservation', 0):.2f}%")
        logger.info(f"Composite Score: {metrics.get('overall', {}).get('composite_score', 0):.2f}%")
        
        print("\n=== Translation Evaluation Summary ===")
        print(f"BERT Score: {metrics.get('overall', {}).get('bert_score', 0):.2f}%")
        print(f"BLEU Score: {metrics.get('overall', {}).get('bleu_score', 0):.2f}%")
        print(f"English Preservation: {metrics.get('overall', {}).get('english_preservation', 0):.2f}%")
        print(f"Composite Score: {metrics.get('overall', {}).get('composite_score', 0):.2f}%")
        print("\nOutput files:")
        print(f"- Translated data: {translated_file}")
        print(f"- Back-translated data: {back_translated_file}")
        print(f"- Metrics: {metrics_file}")
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        print("\n=== Translation Evaluation Summary ===")
        print(f"Error calculating metrics: {e}")
        print("Make sure all required packages are installed in your environment")
    
    print(f"\nTranslated file: {translated_file}")
    print(f"Back-translated file: {back_translated_file}")
    if 'metrics_file' in locals():
        print(f"Metrics file: {metrics_file}")

if __name__ == "__main__":
    main()
