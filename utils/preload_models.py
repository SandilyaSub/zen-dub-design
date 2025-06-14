"""
Preload and verify NLP models and dependencies.

This script preloads the BERT model and verifies that all required
dependencies for translation metrics are correctly installed.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def preload_bert_model():
    """Preload the BERT model to avoid runtime downloads."""
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading distilbert-base-multilingual-cased model...")
        model = SentenceTransformer('distilbert-base-multilingual-cased')
        logger.info(f"Successfully loaded BERT model with {model.get_sentence_embedding_dimension()} dimensions")
        return True
    except ImportError:
        logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
        return False
    except Exception as e:
        logger.error(f"Error loading BERT model: {str(e)}")
        return False

def verify_sacrebleu():
    """Verify that sacrebleu is correctly installed."""
    try:
        import sacrebleu
        logger.info(f"Successfully loaded sacrebleu version {sacrebleu.__version__}")
        return True
    except ImportError:
        logger.error("sacrebleu not installed. Install with: pip install sacrebleu")
        return False
    except Exception as e:
        logger.error(f"Error loading sacrebleu: {str(e)}")
        return False

def verify_all_dependencies():
    """Verify all required dependencies for translation metrics."""
    dependencies = {
        "sentence-transformers": preload_bert_model,
        "sacrebleu": verify_sacrebleu
    }
    
    all_success = True
    for name, verify_func in dependencies.items():
        logger.info(f"Verifying {name}...")
        if not verify_func():
            all_success = False
            logger.error(f"Failed to verify {name}")
        else:
            logger.info(f"Successfully verified {name}")
    
    return all_success

if __name__ == "__main__":
    logger.info("Starting dependency verification...")
    success = verify_all_dependencies()
    if success:
        logger.info("All dependencies verified successfully")
        sys.exit(0)
    else:
        logger.error("Some dependencies failed verification")
        sys.exit(1)
