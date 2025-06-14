"""
Secret Manager Utility

This module provides functions to securely access API keys and other secrets
from either environment variables (for local development) or Google Secret Manager (for production).
"""

import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

# Cache for secrets to avoid repeated API calls
_secret_cache = {}

# Define environment variable names and their corresponding secret IDs
SECRET_MAPPING = {
    'sarvam-api-key': 'SARVAM_API_KEY',
    'gemini-api-key': 'GEMINI_API_KEY',
    'cartesia-api-key': 'CARTESIA_API_KEY',
    'cartesia-api-version': 'CARTESIA_API_VERSION',
    'youtube-api-key': 'YOUTUBE_API_KEY'
}

def get_secret(secret_id, project_id=None):
    """
    Get a secret from environment variables (for local development)
    or Google Secret Manager (for production).
    
    Args:
        secret_id (str): ID of the secret (e.g., 'sarvam-api-key')
        project_id (str, optional): Google Cloud project ID
        
    Returns:
        str: The secret value or None if not found
    """
    # Check cache first
    if secret_id in _secret_cache:
        logger.info(f"Using cached value for {secret_id}")
        return _secret_cache[secret_id]
    
    logger.info(f"Retrieving secret: {secret_id}, project_id: {project_id}")
    
    # Try environment variable first (for local development)
    # Map from secret ID to environment variable name
    env_var = SECRET_MAPPING.get(secret_id, secret_id.replace('-', '_').upper())
    secret_value = os.environ.get(env_var)
    
    if secret_value:
        logger.info(f"Found {env_var} in environment variables with length: {len(secret_value)}")
        # Check for placeholder or invalid values
        if secret_value == "placeholder" or secret_value.startswith("your") or secret_value == "your-api-key-here":
            logger.warning(f"Found placeholder value '{secret_value}' for {env_var}, will try Secret Manager instead")
        else:
            logger.info(f"Using valid environment variable for {env_var}")
            _secret_cache[secret_id] = secret_value
            return secret_value
    else:
        logger.info(f"Environment variable {env_var} not found")
    
    # Fall back to Secret Manager (for production)
    try:
        # Only import google-cloud-secret-manager when needed
        logger.info(f"Trying to access Secret Manager for {secret_id}")
        from google.cloud import secretmanager
        
        # Use provided project ID or try to get it from metadata server
        if not project_id:
            import requests
            try:
                logger.info("Getting project ID from metadata server")
                project_id = requests.get(
                    "http://metadata.google.internal/computeMetadata/v1/project/project-id",
                    headers={"Metadata-Flavor": "Google"},
                    timeout=2
                ).text
                logger.info(f"Got project ID from metadata: {project_id}")
            except Exception as e:
                logger.warning(f"Could not get project ID from metadata: {str(e)}")
                # If we can't get from metadata, try default credentials
                try:
                    import google.auth
                    _, project_id = google.auth.default()
                    logger.info(f"Got project ID from default credentials: {project_id}")
                except Exception as e:
                    logger.error(f"Could not determine project ID: {str(e)}")
                    return None
        
        if not project_id:
            logger.error("No project ID available, cannot access Secret Manager")
            return None
        
        # Create the Secret Manager client and access the secret
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        logger.info(f"Accessing secret at: {name}")
        
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        
        # Cache the result
        _secret_cache[secret_id] = secret_value
        logger.info(f"Successfully retrieved {secret_id} from Secret Manager with length: {len(secret_value)}")
        
        return secret_value
        
    except ImportError as e:
        logger.warning(f"Google Cloud Secret Manager not installed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
        
        # If we failed to get from Secret Manager, check if we have a placeholder value
        env_mapping = {
            'sarvam-api-key': 'SARVAM_API_KEY',
            'gemini-api-key': 'GEMINI_API_KEY',
            'cartesia-api-key': 'CARTESIA_API_KEY',
            'cartesia-api-version': 'CARTESIA_API_VERSION',
            'youtube-api-key': 'YOUTUBE_API_KEY'
        }
        env_var = env_mapping.get(secret_id, secret_id.replace('-', '_').upper())
        secret_value = os.environ.get(env_var)
        
        if secret_value:
            # Check if it's a placeholder or invalid value
            if secret_value == "placeholder" or secret_value.startswith("your") or secret_value == "your-api-key-here":
                logger.error(f"Only found placeholder value '{secret_value}' for {env_var} after Secret Manager failure")
                # For Gemini API, don't return placeholder values as they cause API errors
                if secret_id == "gemini-api-key":
                    logger.error("Not returning placeholder Gemini API key as it would cause API errors")
                    return None
            logger.warning(f"Using environment value for {env_var} after Secret Manager failure")
            return secret_value
        
        return None
