"""
Translation quality metrics module for evaluating translation quality.

This module provides functions for calculating BERT and BLEU scores
for translation quality assessment using back-translation.
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables for models
sentence_transformer = None
bert_tokenizer = None
bert_model = None

# Language code mapping
LANGUAGE_MAP = {
    'hindi': 'hi-IN',
    'telugu': 'te-IN',
    'english': 'en-IN',
    'tamil': 'ta-IN',
    'kannada': 'kn-IN',
    'malayalam': 'ml-IN',
    'bengali': 'bn-IN',
    'marathi': 'mr-IN',
    'gujarati': 'gu-IN',
    'punjabi': 'pa-IN',
    'odia': 'or-IN',
    'urdu': 'ur-IN',
}

# Mapping from code to language name
CODE_TO_LANGUAGE_NAME = {
    'hi-IN': 'Hindi',
    'te-IN': 'Telugu',
    'en-IN': 'English',
    'ta-IN': 'Tamil',
    'kn-IN': 'Kannada',
    'ml-IN': 'Malayalam',
    'bn-IN': 'Bengali',
    'mr-IN': 'Marathi',
    'gu-IN': 'Gujarati',
    'pa-IN': 'Punjabi',
    'or-IN': 'Odia',
    'ur-IN': 'Urdu',
}

# Reverse mapping for code to name
LANGUAGE_CODE_TO_NAME = {code.split('-')[0]: name for name, code in LANGUAGE_MAP.items()}

def normalize_language_code(lang: str) -> str:
    """
    Normalize language representation to standard BCP-47 code.
    
    Args:
        lang: Language name or code
        
    Returns:
        Normalized language code with region (BCP-47 format)
    """
    if not lang:
        return "en-IN"  # Default to English
        
    # Convert to lowercase for case-insensitive matching
    lang_lower = lang.lower()
    
    # If it's a language name, convert to code with region
    if lang_lower in LANGUAGE_MAP:
        return LANGUAGE_MAP[lang_lower]
    
    # If it's a simple language code (e.g., 'hi'), add region
    if lang_lower in ['hi', 'te', 'en', 'ta', 'kn', 'ml', 'bn', 'mr', 'gu', 'pa', 'or', 'ur']:
        return f"{lang_lower}-IN"
    
    # If it's already a code with region suffix (e.g., 'hi-IN'), return as is
    if '-' in lang_lower:
        return lang_lower
    
    # Try to find a matching language code prefix
    for code in LANGUAGE_MAP.values():
        if code.startswith(f"{lang_lower}-"):
            return code
    
    # If we can't normalize it, return as is with a warning
    logger.warning(f"Could not normalize language code: {lang}, using as is")
    return lang

def get_language_name(lang_code: str) -> str:
    """
    Convert a language code to a language name for use with the Google Translate API.
    
    Args:
        lang_code: Language code (e.g., 'hi-IN')
        
    Returns:
        Language name (e.g., 'Hindi')
    """
    # Standardize the code format
    normalized_code = normalize_language_code(lang_code)
    
    # Get the language name from the mapping
    if normalized_code in CODE_TO_LANGUAGE_NAME:
        return CODE_TO_LANGUAGE_NAME[normalized_code]
    
    # If not found in mapping, try to extract from the code
    if normalized_code.startswith('hi-'):
        return 'Hindi'
    elif normalized_code.startswith('te-'):
        return 'Telugu'
    elif normalized_code.startswith('en-'):
        return 'English'
    elif normalized_code.startswith('ta-'):
        return 'Tamil'
    elif normalized_code.startswith('kn-'):
        return 'Kannada'
    elif normalized_code.startswith('ml-'):
        return 'Malayalam'
    elif normalized_code.startswith('bn-'):
        return 'Bengali'
    elif normalized_code.startswith('mr-'):
        return 'Marathi'
    elif normalized_code.startswith('gu-'):
        return 'Gujarati'
    elif normalized_code.startswith('pa-'):
        return 'Punjabi'
    elif normalized_code.startswith('or-'):
        return 'Odia'
    elif normalized_code.startswith('ur-'):
        return 'Urdu'
    
    # If we can't determine the language name, use the code as is
    logger.warning(f"Could not determine language name for code: {lang_code}, using as is")
    return lang_code

def get_sentence_transformer():
    """Get or initialize the sentence transformer model."""
    global sentence_transformer
    
    if sentence_transformer is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Initializing Sentence Transformer model")
            sentence_transformer = SentenceTransformer('distilbert-base-multilingual-cased')
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
    
    return sentence_transformer

def calculate_bert_similarity(text1: str, text2: str) -> float:
    """
    Calculate semantic similarity between two texts using BERT embeddings.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        # Skip empty texts
        if not text1 or not text2:
            logger.warning("Empty text provided for BERT similarity calculation")
            return 0.0
        
        # Get model
        model = get_sentence_transformer()
        
        # Get embeddings
        embedding1 = model.encode([text1])[0]
        embedding2 = model.encode([text2])[0]
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity([embedding1], [embedding2])[0][0]
        
        return float(similarity)
    except Exception as e:
        logger.error(f"Error calculating BERT similarity: {e}")
        return 0.0

def calculate_bleu_score(reference: str, hypothesis: str) -> float:
    """
    Calculate BLEU score between reference and hypothesis texts.
    
    Args:
        reference: Reference text
        hypothesis: Hypothesis text
        
    Returns:
        BLEU score (0-100)
    """
    try:
        # Skip empty texts
        if not reference or not hypothesis:
            logger.warning("Empty text provided for BLEU calculation")
            return 0.0
        
        # Import sacrebleu
        try:
            from sacrebleu import corpus_bleu
        except ImportError:
            logger.error("sacrebleu not installed. Install with: pip install sacrebleu")
            raise
        
        # Calculate BLEU score
        bleu = corpus_bleu([hypothesis], [[reference]]).score
        
        return float(bleu)
    except Exception as e:
        logger.error(f"Error calculating BLEU score: {e}")
        return 0.0

def back_translate_content(translated_data: Dict[str, Any], 
                          target_lang_code: str, 
                          source_lang_code: str) -> Dict[str, Any]:
    """
    Back-translate the translated content to the original language.
    
    Args:
        translated_data: Dictionary containing translated segments
        target_lang_code: Original target language code (e.g., 'te-IN')
        source_lang_code: Original source language code (e.g., 'hi-IN')
        
    Returns:
        Dictionary with back-translated content
    """
    try:
        # Import translation function
        from modules.google_translation import translate_text
        
        # Normalize language codes
        normalized_source = normalize_language_code(source_lang_code)
        normalized_target = normalize_language_code(target_lang_code)
        
        # Convert to language names for Google Translate API
        source_lang_name = get_language_name(normalized_source)
        target_lang_name = get_language_name(normalized_target)
        
        logger.info(f"Normalized language codes - Source: {source_lang_code} → {normalized_source} ({source_lang_name}), "
                   f"Target: {target_lang_code} → {normalized_target} ({target_lang_name})")
        
        # Initialize result structure
        back_translated = {
            "transcript": translated_data.get("transcript", ""),
            "segments": [],
            "back_translated_transcript": "",
            "source_language": normalized_target,  # For back-translation, target becomes source
            "target_language": normalized_source   # For back-translation, source becomes target
        }
        
        # Back-translate full transcript
        logger.info(f"Back-translating full transcript from {target_lang_name} to {source_lang_name}")
        full_translated_text = translated_data.get("translated_transcript", "")
        
        if full_translated_text:
            back_translated_text = translate_text(
                full_translated_text, 
                source_lang=target_lang_name,  # The translated text is in target language
                target_lang=source_lang_name   # We want to translate back to source language
            )
            back_translated["back_translated_transcript"] = back_translated_text
        
        # Back-translate each segment
        logger.info(f"Back-translating {len(translated_data.get('segments', []))} segments")
        for segment in translated_data.get("segments", []):
            translated_text = segment.get("translated_text", "")
            
            if translated_text:
                back_translated_segment = translate_text(
                    translated_text,
                    source_lang=target_lang_name,  # The translated text is in target language
                    target_lang=source_lang_name   # We want to translate back to source language
                )
            else:
                back_translated_segment = ""
            
            back_translated["segments"].append({
                "segment_id": segment.get("segment_id", ""),
                "text": segment.get("text", ""),  # Original text
                "translated_text": segment.get("translated_text", ""),  # Target language
                "back_translated_text": back_translated_segment,  # Back to source language
                "duration": segment.get("duration", 0),
                "start_time": segment.get("start_time", 0),
                "end_time": segment.get("end_time", 0)
            })
        
        return back_translated
    
    except Exception as e:
        logger.error(f"Error in back-translation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Return minimal structure to prevent downstream errors
        return {
            "transcript": translated_data.get("transcript", ""),
            "segments": [],
            "back_translated_transcript": "",
            "source_language": target_lang_code,
            "target_language": source_lang_code
        }

def calculate_bert_scores(original_data: Dict[str, Any], 
                         back_translated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate BERT scores for overall text and segment-wise.
    
    Args:
        original_data: Dictionary with original text
        back_translated_data: Dictionary with back-translated text
        
    Returns:
        Dictionary with BERT scores
    """
    try:
        logger.info("Calculating BERT scores")
        
        # Calculate overall BERT score
        original_transcript = original_data.get("transcript", "")
        back_transcript = back_translated_data.get("back_translated_transcript", "")
        
        overall_bert = 0.0
        if original_transcript and back_transcript:
            overall_bert = calculate_bert_similarity(original_transcript, back_transcript)
            logger.info(f"Overall BERT score: {overall_bert:.4f}")
        
        # Calculate segment-wise BERT scores
        segment_scores = []
        total_duration = 0
        
        for i, orig_segment in enumerate(original_data.get("segments", [])):
            # Skip if index is out of range
            if i >= len(back_translated_data.get("segments", [])):
                continue
                
            # Find corresponding back-translated segment
            back_segment = back_translated_data["segments"][i]
            
            # Get original and back-translated text
            orig_text = orig_segment.get("text", "")
            back_text = back_segment.get("back_translated_text", "")
            
            # Skip empty segments
            if not orig_text or not back_text:
                continue
                
            # Calculate similarity
            similarity = calculate_bert_similarity(orig_text, back_text)
            
            # Get segment duration for weighting
            duration = float(orig_segment.get("duration", 0))
            total_duration += duration
            
            segment_scores.append({
                "segment_id": orig_segment.get("segment_id", ""),
                "bert_score": similarity,
                "duration": duration
            })
        
        # Calculate weighted average
        weighted_bert = 0.0
        if total_duration > 0 and segment_scores:
            weighted_bert = sum(s["bert_score"] * s["duration"] for s in segment_scores) / total_duration
            logger.info(f"Weighted segment BERT score: {weighted_bert:.4f}")
        
        return {
            "bert_overall": float(overall_bert * 100),  # Scale to 0-100
            "bert_segment_weighted": float(weighted_bert * 100),  # Scale to 0-100
            "bert_segments": segment_scores
        }
    
    except Exception as e:
        logger.error(f"Error calculating BERT scores: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "bert_overall": 0.0,
            "bert_segment_weighted": 0.0,
            "bert_segments": []
        }

def calculate_bleu_scores(original_data: Dict[str, Any], 
                         back_translated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate BLEU scores for overall text and segment-wise.
    
    Args:
        original_data: Dictionary with original text
        back_translated_data: Dictionary with back-translated text
        
    Returns:
        Dictionary with BLEU scores
    """
    try:
        logger.info("Calculating BLEU scores")
        
        # Calculate overall BLEU score
        original_transcript = original_data.get("transcript", "")
        back_transcript = back_translated_data.get("back_translated_transcript", "")
        
        overall_bleu = 0.0
        if original_transcript and back_transcript:
            overall_bleu = calculate_bleu_score(original_transcript, back_transcript)
            logger.info(f"Overall BLEU score: {overall_bleu:.4f}")
        
        # Calculate segment-wise BLEU scores
        segment_scores = []
        total_duration = 0
        
        for i, orig_segment in enumerate(original_data.get("segments", [])):
            # Skip if index is out of range
            if i >= len(back_translated_data.get("segments", [])):
                continue
                
            # Find corresponding back-translated segment
            back_segment = back_translated_data["segments"][i]
            
            # Get original and back-translated text
            orig_text = orig_segment.get("text", "")
            back_text = back_segment.get("back_translated_text", "")
            
            # Skip empty segments
            if not orig_text or not back_text:
                continue
                
            # Calculate BLEU score
            bleu = calculate_bleu_score(orig_text, back_text)
            
            # Get segment duration for weighting
            duration = float(orig_segment.get("duration", 0))
            total_duration += duration
            
            segment_scores.append({
                "segment_id": orig_segment.get("segment_id", ""),
                "bleu_score": bleu,
                "duration": duration
            })
        
        # Calculate weighted average
        weighted_bleu = 0.0
        if total_duration > 0 and segment_scores:
            weighted_bleu = sum(s["bleu_score"] * s["duration"] for s in segment_scores) / total_duration
            logger.info(f"Weighted segment BLEU score: {weighted_bleu:.4f}")
        
        return {
            "bleu_overall": float(overall_bleu),
            "bleu_segment_weighted": float(weighted_bleu),
            "bleu_segments": segment_scores
        }
    
    except Exception as e:
        logger.error(f"Error calculating BLEU scores: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "bleu_overall": 0.0,
            "bleu_segment_weighted": 0.0,
            "bleu_segments": []
        }

def compute_enhanced_composite_metric(metrics: Dict[str, Any]) -> float:
    """
    Calculate enhanced composite metric including BERT and BLEU scores.
    
    Args:
        metrics: Dictionary with all metrics
        
    Returns:
        Composite score (0-1)
    """
    try:
        weights = {
            "semantic": 0.15,
            "bert_overall": 0.25,
            "bleu_overall": 0.20,
            "bert_segment_weighted": 0.15,
            "bleu_segment_weighted": 0.10,
            "diarization": 0.15
        }
        
        # Normalize scores (0-100 to 0-1)
        bert_overall_norm = metrics.get("bert_overall", 0) / 100
        bert_segment_norm = metrics.get("bert_segment_weighted", 0) / 100
        bleu_overall_norm = metrics.get("bleu_overall", 0) / 100
        bleu_segment_norm = metrics.get("bleu_segment_weighted", 0) / 100
        
        score = (
            weights["semantic"] * metrics.get("semantic", 0.0) +
            weights["bert_overall"] * bert_overall_norm +
            weights["bleu_overall"] * bleu_overall_norm +
            weights["bert_segment_weighted"] * bert_segment_norm +
            weights["bleu_segment_weighted"] * bleu_segment_norm +
            weights["diarization"] * metrics.get("diarization", 0.0)
        )
        
        return float(score)
    
    except Exception as e:
        logger.error(f"Error computing enhanced composite metric: {e}")
        return 0.0

def evaluate_translation_quality(session_id: str, base_dir: str = "outputs") -> Dict[str, Any]:
    """
    Evaluate translation quality using BERT and BLEU scores with back-translation.
    
    Args:
        session_id: Session ID
        base_dir: Base directory for outputs
        
    Returns:
        Dictionary with evaluation results
    """
    try:
        logger.info(f"Evaluating translation quality for session {session_id}")
        
        # Load original data
        diarization_path = os.path.join(base_dir, session_id, "diarization.json")
        if not os.path.exists(diarization_path):
            logger.error(f"Diarization file not found: {diarization_path}")
            return {"error": "Diarization file not found"}
            
        with open(diarization_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # Load translated data
        translation_path = os.path.join(base_dir, session_id, "diarization_translated.json")
        if not os.path.exists(translation_path):
            logger.error(f"Translation file not found: {translation_path}")
            return {"error": "Translation file not found"}
            
        with open(translation_path, 'r', encoding='utf-8') as f:
            translated_data = json.load(f)
        
        # Load metadata if available
        metadata_path = os.path.join(base_dir, session_id, "metadata.json")
        metadata = {}
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                logger.info(f"Loaded metadata for session {session_id}")
            except Exception as e:
                logger.warning(f"Error loading metadata: {e}")
        
        # IMPROVED LANGUAGE DETERMINATION LOGIC
        # 1. First try to get languages from translated_data
        target_lang = translated_data.get("target_language")
        source_lang = translated_data.get("source_language")
        
        # 2. If not available, try to get from metadata
        if not target_lang and "target_language" in metadata:
            target_lang = metadata.get("target_language")
            logger.info(f"Using target language from metadata: {target_lang}")
        
        if not source_lang and "source_language" in metadata:
            source_lang = metadata.get("source_language")
            logger.info(f"Using source language from metadata: {source_lang}")
        
        # 3. Default values if still not available
        if not target_lang:
            target_lang = "hindi"  # Default target
            logger.warning(f"Target language not found in data or metadata, using default: {target_lang}")
            
        if not source_lang:
            source_lang = "telugu"  # Default source
            logger.warning(f"Source language not found in data or metadata, using default: {source_lang}")
        
        # Normalize language codes
        normalized_source = normalize_language_code(source_lang)
        normalized_target = normalize_language_code(target_lang)
        
        # Get language names for logging
        source_lang_name = get_language_name(normalized_source)
        target_lang_name = get_language_name(normalized_target)
        
        logger.info(f"Determined source language: {source_lang} → {normalized_source} ({source_lang_name}), "
                   f"Target language: {target_lang} → {normalized_target} ({target_lang_name})")
        
        # Validate that source and target languages are different
        if normalized_source == normalized_target:
            logger.error(f"Source and target languages are the same: {normalized_source}")
            return {"error": "Source and target languages must be different for back-translation"}
        
        # Update the translated data with the correct source language
        translated_data["source_language"] = normalized_source
        translated_data["target_language"] = normalized_target
        
        # Perform back-translation
        back_translated_data = back_translate_content(
            translated_data, 
            target_lang_code=normalized_target, 
            source_lang_code=normalized_source
        )
        
        # Calculate BERT scores
        bert_scores = calculate_bert_scores(original_data, back_translated_data)
        
        # Calculate BLEU scores
        bleu_scores = calculate_bleu_scores(original_data, back_translated_data)
        
        # Prepare final result
        evaluation_result = {
            **bert_scores,
            **bleu_scores,
            "back_translation": {
                "transcript": back_translated_data.get("back_translated_transcript", "")
            }
        }
        
        logger.info(f"Translation quality evaluation completed for session {session_id}")
        return evaluation_result
    
    except Exception as e:
        logger.error(f"Error evaluating translation quality: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}
