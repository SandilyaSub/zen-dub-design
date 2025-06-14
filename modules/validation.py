import os
import logging
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from jiwer import wer

# Import translation metrics module
from modules.translation_metrics import (
    evaluate_translation_quality,
    compute_enhanced_composite_metric
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variables for models
tfidf_vectorizer = None

def _get_tfidf_vectorizer():
    """Get or initialize the TF-IDF vectorizer."""
    global tfidf_vectorizer
    
    if tfidf_vectorizer is None:
        logger.info("Initializing TF-IDF vectorizer")
        tfidf_vectorizer = TfidfVectorizer()
    
    return tfidf_vectorizer

def calculate_similarity(source_text, target_text):
    """
    Calculate similarity score between source and target text using TF-IDF and cosine similarity.
    
    Args:
        source_text: Source text
        target_text: Target text
        
    Returns:
        similarity_score: Similarity score between 0 and 1
    """
    try:
        logger.info("Calculating similarity between texts")
        
        # Handle empty text
        if not source_text or not target_text:
            logger.warning("Empty text provided for similarity calculation")
            return 0.0
        
        # Combine texts for fitting the vectorizer
        texts = [source_text, target_text]
        
        # Get vectorizer
        vectorizer = _get_tfidf_vectorizer()
        
        # Transform texts to TF-IDF vectors
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Calculate cosine similarity
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        logger.info(f"Similarity score: {similarity:.4f}")
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0

def validate_translation(source_text, translated_text, source_lang, target_lang):
    """
    Validate translation quality.
    
    Args:
        source_text: Source text
        translated_text: Translated text
        source_lang: Source language
        target_lang: Target language
        
    Returns:
        validation_result: Dictionary with validation metrics
    """
    try:
        logger.info(f"Validating translation from {source_lang} to {target_lang}")
        
        # Calculate text similarity (this is a proxy for translation quality)
        similarity_score = calculate_similarity(source_text, translated_text)
        
        # Calculate other metrics
        source_length = len(source_text.split())
        target_length = len(translated_text.split())
        length_ratio = target_length / source_length if source_length > 0 else 0
        
        # Prepare validation result
        validation_result = {
            "similarity_score": similarity_score,
            "source_length": source_length,
            "target_length": target_length,
            "length_ratio": length_ratio,
            "quality_rating": _get_quality_rating(similarity_score, length_ratio)
        }
        
        logger.info(f"Validation complete: {validation_result}")
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating translation: {e}")
        return {
            "similarity_score": 0.0,
            "source_length": 0,
            "target_length": 0,
            "length_ratio": 0.0,
            "quality_rating": "Unknown"
        }

def _get_quality_rating(similarity_score, length_ratio):
    """Get quality rating based on similarity score and length ratio."""
    # This is a simple heuristic and can be improved
    if similarity_score < 0.3:
        return "Poor"
    elif similarity_score < 0.5:
        return "Fair"
    elif similarity_score < 0.7:
        return "Good"
    else:
        return "Excellent"

def compute_transcription_edit(ref, hyp):
    """Compute Word Error Rate (WER) between reference and hypothesis transcripts."""
    try:
        return wer(ref, hyp)
    except Exception as e:
        logger.error(f"Error computing transcription edit distance: {e}")
        return 1.0

def compute_translation_edit(ref, hyp):
    """Compute WER between reference and hypothesis translations."""
    try:
        return wer(ref, hyp)
    except Exception as e:
        logger.error(f"Error computing translation edit distance: {e}")
        return 1.0

def compute_speaker_change_accuracy(ref_changes, hyp_changes):
    """Compare number of speaker changes in reference and hypothesis."""
    try:
        # Both empty: perfect match
        if not ref_changes and not hyp_changes:
            return 1.0
        # Only one is empty: total mismatch
        if not ref_changes or not hyp_changes:
            return 0.0
        return min(len(ref_changes), len(hyp_changes)) / max(len(ref_changes), len(hyp_changes))
    except Exception as e:
        logger.error(f"Error computing speaker change accuracy: {e}")
        return 0.0

def compute_composite_metric(metrics, weights=None):
    """Aggregate metrics into a composite score (all metric values normalized 0-1)."""
    if weights is None:
        weights = {"semantic": 0.3, "transcription": 0.2, "diarization": 0.2, "translation": 0.3}
    score = (
        weights["semantic"] * metrics.get("semantic", 0.0) +
        weights["transcription"] * (1 - metrics.get("transcription_edit", 1.0)) +
        weights["diarization"] * metrics.get("diarization", 0.0) +
        weights["translation"] * (1 - metrics.get("translation_edit", 1.0))
    )
    return score

def compute_audio_extraction_composite(metrics):
    """
    Calculate composite score using only BERT and BLEU metrics with specified weights.
    
    Args:
        metrics: Dictionary containing all metrics
        
    Returns:
        Composite score (0-100)
    """
    # Get segment-weighted scores
    bert_score = metrics.get("bert_segment_weighted", 0)
    bleu_score = metrics.get("bleu_segment_weighted", 0)
    
    # Apply weights (0.7 for BERT, 0.3 for BLEU)
    composite_score = (0.7 * bert_score) + (0.3 * bleu_score)
    
    logger.info(f"Audio extraction composite score: {composite_score:.2f} (BERT: {bert_score:.2f} * 0.7 + BLEU: {bleu_score:.2f} * 0.3)")
    
    return float(composite_score)

def save_validation_results(session_id, results, base_dir="outputs"):
    """Save validation results as JSON in /outputs/<session_id>/validation.json."""
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    validation_path = os.path.join(session_dir, "validation.json")
    try:
        with open(validation_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Validation results saved to {validation_path}")
    except Exception as e:
        logger.error(f"Error saving validation results: {e}")

def validate_translation_with_metrics(session_id, base_dir="outputs"):
    """
    Validate translation using multiple metrics including BERT and BLEU scores.
    
    Args:
        session_id: Session ID
        base_dir: Base directory for outputs
        
    Returns:
        Dictionary with validation results
    """
    try:
        logger.info(f"Validating translation with advanced metrics for session {session_id}")
        
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
        
        # Calculate traditional metrics
        source_text = original_data.get("transcript", "")
        translated_text = translated_data.get("translated_transcript", "")
        source_lang = translated_data.get("source_language", "hi")
        target_lang = translated_data.get("target_language", "te")
        
        # Basic semantic similarity
        semantic_similarity = calculate_similarity(source_text, translated_text)
        
        # Calculate speaker changes
        ref_speakers = [s.get("speaker", "") for s in original_data.get("segments", [])]
        hyp_speakers = [s.get("speaker", "") for s in translated_data.get("segments", [])]
        
        ref_changes = [i for i in range(1, len(ref_speakers)) if ref_speakers[i] != ref_speakers[i-1]]
        hyp_changes = [i for i in range(1, len(hyp_speakers)) if hyp_speakers[i] != hyp_speakers[i-1]]
        
        diarization_score = compute_speaker_change_accuracy(ref_changes, hyp_changes)
        
        # Calculate edit distances
        transcription_edit = compute_transcription_edit(source_text, source_text)  # Placeholder, should be ASR vs reference
        translation_edit = compute_translation_edit(source_text, translated_text)  # Using source vs translation as proxy
        
        # Collect traditional metrics
        traditional_metrics = {
            "semantic": semantic_similarity,
            "transcription_edit": transcription_edit,
            "diarization": diarization_score,
            "translation_edit": translation_edit
        }
        
        # Calculate composite score from traditional metrics
        traditional_composite = compute_composite_metric(traditional_metrics)
        
        # Get advanced metrics (BERT and BLEU)
        advanced_metrics = evaluate_translation_quality(session_id, base_dir)
        
        # Combine all metrics
        all_metrics = {
            **traditional_metrics,
            **advanced_metrics
        }
        
        # Calculate enhanced composite score
        enhanced_composite = compute_enhanced_composite_metric(all_metrics)
        
        # Calculate the new audio extraction composite score
        audio_extraction_composite = compute_audio_extraction_composite(advanced_metrics)
        
        # Prepare final result
        validation_result = {
            "metrics": all_metrics,
            "traditional_composite_score": traditional_composite,
            "enhanced_composite_score": enhanced_composite,
            "audio_extraction_score": audio_extraction_composite,
            "audio_extraction_weights": {
                "bert": 0.7,
                "bleu": 0.3
            }
        }
        
        # Save results
        save_validation_results(session_id, validation_result, base_dir)
        
        logger.info(f"Advanced validation completed for session {session_id}")
        return validation_result
        
    except Exception as e:
        logger.error(f"Error in advanced validation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}
