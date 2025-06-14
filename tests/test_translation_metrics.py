#!/usr/bin/env python3
"""
Test script for translation metrics module.
This script tests the BERT and BLEU score calculation functionality
using back-translation on an existing session.
"""

import os
import sys
import json
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_translation_metrics(session_id):
    """
    Test translation metrics on a specific session.
    
    Args:
        session_id: Session ID to test
    """
    try:
        from modules.validation import validate_translation_with_metrics
        
        logger.info(f"Testing translation metrics on session {session_id}")
        
        # Check if session exists
        base_dir = "outputs"
        session_dir = os.path.join(base_dir, session_id)
        
        if not os.path.exists(session_dir):
            logger.error(f"Session directory not found: {session_dir}")
            return False
            
        # Check if required files exist
        diarization_path = os.path.join(session_dir, "diarization.json")
        translation_path = os.path.join(session_dir, "diarization_translated.json")
        
        if not os.path.exists(diarization_path):
            logger.error(f"Diarization file not found: {diarization_path}")
            return False
            
        if not os.path.exists(translation_path):
            logger.error(f"Translation file not found: {translation_path}")
            return False
        
        # Run validation
        logger.info("Running translation validation with advanced metrics")
        validation_result = validate_translation_with_metrics(session_id, base_dir)
        
        # Print results
        logger.info("Validation results:")
        logger.info(f"BERT overall score: {validation_result.get('metrics', {}).get('bert_overall', 0):.4f}")
        logger.info(f"BERT segment weighted score: {validation_result.get('metrics', {}).get('bert_segment_weighted', 0):.4f}")
        logger.info(f"BLEU overall score: {validation_result.get('metrics', {}).get('bleu_overall', 0):.4f}")
        logger.info(f"BLEU segment weighted score: {validation_result.get('metrics', {}).get('bleu_segment_weighted', 0):.4f}")
        logger.info(f"Enhanced composite score: {validation_result.get('enhanced_composite_score', 0):.4f}")
        
        # Save detailed results to a test output file
        output_path = os.path.join(session_dir, "test_validation_results.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(validation_result, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Detailed results saved to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error testing translation metrics: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test translation metrics on a session")
    parser.add_argument("session_id", help="Session ID to test")
    args = parser.parse_args()
    
    success = test_translation_metrics(args.session_id)
    
    if success:
        logger.info("Test completed successfully")
    else:
        logger.error("Test failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
