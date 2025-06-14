#!/usr/bin/env python3
"""
Test script for OpenAI translation module.

This script tests the OpenAI translation module by:
1. Translating a diarization JSON file from source to target language
2. Back-translating the result to the source language
3. Calculating translation metrics (BERT, BLEU, English preservation)
4. Saving the results to output files

Usage:
    python3 tests/test_openai_translation.py --input_file /path/to/diarization.json --source_language hindi --target_language english --api_key YOUR_OPENAI_API_KEY
"""

import os
import sys
import json
import argparse
import datetime
import logging
import copy
from pathlib import Path
import getpass

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import translation modules
from modules.openai_translation import (
    openai_translate_diarized_content,
    openai_back_translate,
    openai_translate_diarized_content_context_aware
)

# Import metrics calculation
from modules.translation_metrics import (
    calculate_bert_scores,
    calculate_bleu_scores
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_english_word_preservation(original_text, translated_text):
    """
    Calculate the percentage of English words preserved in translation.
    
    Args:
        original_text: Original text
        translated_text: Translated text
        
    Returns:
        float: Percentage of English words preserved (0-100)
    """
    # Simple implementation - can be improved with better tokenization
    # This assumes that English words are the same in both texts
    
    # Extract words that look like English (contain only ASCII letters)
    def extract_english_words(text):
        words = text.split()
        english_words = []
        for word in words:
            # Check if word contains only ASCII letters (a rough approximation for English)
            if all(ord(c) < 128 and c.isalpha() for c in word):
                english_words.append(word.lower())
        return english_words
    
    original_english = extract_english_words(original_text)
    translated_english = extract_english_words(translated_text)
    
    # If no English words in original, return 100%
    if not original_english:
        return 100.0
    
    # Count how many original English words are preserved
    preserved_count = 0
    for word in original_english:
        if word in translated_english:
            preserved_count += 1
    
    # Calculate percentage
    preservation_rate = (preserved_count / len(original_english)) * 100
    
    return preservation_rate

def calculate_metrics(original_data, back_translated_data, translated_data=None):
    """
    Calculate translation metrics.
    
    Args:
        original_data: Original diarization data
        back_translated_data: Back-translated diarization data
        translated_data: Translated diarization data (optional)
        
    Returns:
        dict: Metrics data
    """
    # Log data structure for debugging
    logger.info(f"Original data structure: {list(original_data.keys())}")
    logger.info(f"Back-translated data structure: {list(back_translated_data.keys())}")
    
    # Log segment counts
    logger.info(f"Original segments count: {len(original_data.get('segments', []))}")
    logger.info(f"Back-translated segments count: {len(back_translated_data.get('segments', []))}")
    
    # Check if back_translated_text field exists in segments
    if back_translated_data.get('segments') and 'back_translated_text' in back_translated_data['segments'][0]:
        logger.info("back_translated_text field exists in segments")
    
    # Check if back_translated_transcript field exists
    if 'back_translated_transcript' in back_translated_data:
        logger.info("back_translated_transcript field exists")
    
    # Calculate BERT scores
    bert_scores = calculate_bert_scores(original_data, back_translated_data)
    
    # Calculate BLEU scores
    bleu_scores = calculate_bleu_scores(original_data, back_translated_data)
    
    # Calculate English word preservation if translated data is provided
    english_preservation = 100.0  # Default to 100%
    if translated_data:
        # Extract original and translated transcripts
        original_transcript = original_data.get("transcript", "")
        translated_transcript = translated_data.get("translated_transcript", "")
        
        # Calculate English word preservation
        english_preservation = calculate_english_word_preservation(
            original_transcript, translated_transcript
        )
    
    # Calculate composite score (weighted average)
    # 40% BERT, 30% BLEU, 30% English preservation
    composite_score = (
        bert_scores.get("bert_overall", 0.0) * 100 * 0.4 +
        bleu_scores.get("bleu_overall", 0.0) * 0.3 +
        english_preservation * 0.3
    )
    
    # Create metrics data
    metrics = {
        "bert_scores": bert_scores,
        "bleu_scores": bleu_scores,
        "english_preservation": english_preservation,
        "overall": {
            "bert_score": bert_scores.get("bert_overall", 0.0) * 100,
            "bleu_score": bleu_scores.get("bleu_overall", 0.0),
            "english_preservation": english_preservation,
            "composite_score": composite_score
        }
    }
    
    return metrics

def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test OpenAI translation module')
    parser.add_argument('--input_file', required=True, help='Path to diarization JSON file')
    parser.add_argument('--source_language', required=True, help='Source language')
    parser.add_argument('--target_language', required=True, help='Target language')
    parser.add_argument('--api_key', help='OpenAI API key (optional, falls back to env var)')
    parser.add_argument('--context_aware', action='store_true', help='Use context-aware translation')
    args = parser.parse_args()
    
    # Check for API key
    openai_api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.warning("No OpenAI API key found in environment variables or command line arguments")
        openai_api_key = getpass.getpass("Enter your OpenAI API key: ")
        if not openai_api_key:
            logger.error("No OpenAI API key provided. Exiting.")
            sys.exit(1)
        os.environ["OPENAI_API_KEY"] = openai_api_key
    
    # Load diarization data
    logger.info(f"Loading diarization data from {args.input_file}")
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            diarization_data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading diarization data: {e}")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for output files
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Get base filename without extension
    base_filename = Path(args.input_file).stem
    
    # Translate diarization data
    logger.info(f"Translating from {args.source_language} to {args.target_language}")
    try:
        # Choose translation function based on context_aware flag
        if args.context_aware:
            translated_data = openai_translate_diarized_content_context_aware(
                diarization_data,
                args.target_language,
                args.source_language,
                api_key=openai_api_key
            )
        else:
            translated_data = openai_translate_diarized_content(
                diarization_data,
                args.target_language,
                args.source_language,
                api_key=openai_api_key
            )
        
        # Fix naming conventions in translated data
        logger.info("Fixing naming conventions in translated data")
        
        # Create a new structure with the correct naming conventions
        fixed_translated_data = {
            "transcript": diarization_data.get("transcript", ""),
            "segments": [],
            "language_code": diarization_data.get("language_code", ""),
            "translation_info": translated_data.get("translation_info", {})
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
    translated_file = output_dir / f"{base_filename}_openai_translated_{timestamp}.json"
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
        if args.context_aware:
            back_translated_data_raw = openai_translate_diarized_content_context_aware(
                back_translation_input,
                args.source_language,
                args.target_language,
                api_key=openai_api_key
            )
        else:
            back_translated_data_raw = openai_translate_diarized_content(
                back_translation_input,
                args.source_language,
                args.target_language,
                api_key=openai_api_key
            )
        
        # Fix the structure of back-translated data to match what metrics module expects
        logger.info("Fixing back-translated data structure for metrics calculation")
        
        # Create a new structure with the correct naming conventions
        back_translated_data = {
            "transcript": diarization_data.get("transcript", ""),
            "segments": [],
            "language_code": diarization_data.get("language_code", ""),
            "translation_info": back_translated_data_raw.get("translation_info", {})
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
    back_translated_file = output_dir / f"{base_filename}_openai_back_translated_{timestamp}.json"
    logger.info(f"Saving back-translated data to {back_translated_file}")
    with open(back_translated_file, 'w', encoding='utf-8') as f:
        json.dump(back_translated_data, f, ensure_ascii=False, indent=2)
    
    # Calculate metrics
    logger.info("Calculating translation metrics")
    metrics = calculate_metrics(diarization_data, back_translated_data, translated_data)
    
    # Save metrics
    metrics_file = output_dir / f"{base_filename}_openai_metrics_{timestamp}.json"
    logger.info(f"Saving metrics to {metrics_file}")
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    # Log metrics
    logger.info("Translation evaluation complete")
    logger.info(f"BERT Score: {metrics['overall']['bert_score']:.2f}%")
    logger.info(f"BLEU Score: {metrics['overall']['bleu_score']:.2f}%")
    logger.info(f"English Preservation: {metrics['overall']['english_preservation']:.2f}%")
    logger.info(f"Composite Score: {metrics['overall']['composite_score']:.2f}%")
    
    # Print summary
    print("\n=== Translation Evaluation Summary ===")
    print(f"BERT Score: {metrics['overall']['bert_score']:.2f}%")
    print(f"BLEU Score: {metrics['overall']['bleu_score']:.2f}%")
    print(f"English Preservation: {metrics['overall']['english_preservation']:.2f}%")
    print(f"Composite Score: {metrics['overall']['composite_score']:.2f}%")
    print()
    print(f"Translated file: {translated_file}")
    print(f"Back-translated file: {back_translated_file}")
    print(f"Metrics file: {metrics_file}")

if __name__ == "__main__":
    main()
