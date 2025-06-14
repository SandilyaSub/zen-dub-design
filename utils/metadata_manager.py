"""
Metadata Manager Module

This module provides functions for managing metadata in an append-only fashion,
ensuring that metadata fields are only updated, never completely overwritten.
"""

import os
import json
import logging
from datetime import datetime

def update_metadata_field(session_id, field_name, field_value, base_dir="outputs"):
    """
    Update a single field in the metadata file.
    
    Args:
        session_id (str): The session ID
        field_name (str): The name of the field to update
        field_value: The value to set for the field
        base_dir (str): Base directory for outputs
        
    Returns:
        dict: The updated metadata
    """
    # Construct metadata path
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    metadata_path = os.path.join(session_dir, "metadata.json")
    
    # Load existing metadata
    existing_metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            logging.info(f"Loaded existing metadata from {metadata_path}")
        except Exception as e:
            logging.error(f"Error loading existing metadata: {str(e)}")
    
    # Log the change
    old_value = existing_metadata.get(field_name)
    logging.info(f"Updating metadata field '{field_name}': {old_value} -> {field_value}")
    
    # Update only the specified field
    existing_metadata[field_name] = field_value
    
    # Save the updated metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
    
    return existing_metadata

def update_metadata_section(session_id, section_name, section_data, base_dir="outputs"):
    """
    Update a section (dictionary) in the metadata file.
    
    Args:
        session_id (str): The session ID
        section_name (str): The name of the section to update
        section_data (dict): The data to update in the section
        base_dir (str): Base directory for outputs
        
    Returns:
        dict: The updated metadata
    """
    # Construct metadata path
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    metadata_path = os.path.join(session_dir, "metadata.json")
    
    # Load existing metadata
    existing_metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            logging.info(f"Loaded existing metadata from {metadata_path}")
        except Exception as e:
            logging.error(f"Error loading existing metadata: {str(e)}")
    
    # If section doesn't exist, create it
    if section_name not in existing_metadata:
        existing_metadata[section_name] = {}
    elif not isinstance(existing_metadata[section_name], dict):
        # If it exists but is not a dict, convert it to a dict
        existing_metadata[section_name] = {"value": existing_metadata[section_name]}
    
    # Log the change
    for key, value in section_data.items():
        old_value = existing_metadata[section_name].get(key)
        logging.info(f"Updating metadata section '{section_name}.{key}': {old_value} -> {value}")
    
    # Update the section with new data
    existing_metadata[section_name].update(section_data)
    
    # Save the updated metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
    
    return existing_metadata

def update_metadata(session_id, updates, base_dir="outputs"):
    """
    Update multiple fields in the metadata file.
    
    Args:
        session_id (str): The session ID
        updates (dict): Dictionary of fields to update
        base_dir (str): Base directory for outputs
        
    Returns:
        dict: The updated metadata
    """
    # Construct metadata path
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    metadata_path = os.path.join(session_dir, "metadata.json")
    
    # Load existing metadata
    existing_metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            logging.info(f"Loaded existing metadata from {metadata_path}")
        except Exception as e:
            logging.error(f"Error loading existing metadata: {str(e)}")
    
    # Log the changes
    for key, value in updates.items():
        old_value = existing_metadata.get(key)
        logging.info(f"Updating metadata field '{key}': {old_value} -> {value}")
    
    # Update with new metadata
    existing_metadata.update(updates)
    
    # Save the updated metadata
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(existing_metadata, f, ensure_ascii=False, indent=2)
    
    return existing_metadata

def get_metadata_field(session_id, field_name, default=None, base_dir="outputs"):
    """
    Get a field from the metadata file.
    
    Args:
        session_id (str): The session ID
        field_name (str): The name of the field to get
        default: The default value to return if the field doesn't exist
        base_dir (str): Base directory for outputs
        
    Returns:
        The value of the field, or the default if not found
    """
    metadata_path = os.path.join(base_dir, session_id, "metadata.json")
    
    if not os.path.exists(metadata_path):
        return default
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata.get(field_name, default)
    except Exception as e:
        logging.error(f"Error reading metadata: {str(e)}")
        return default

def get_metadata(session_id, base_dir="outputs"):
    """
    Get the entire metadata for a session.
    
    Args:
        session_id (str): The session ID
        base_dir (str): Base directory for outputs
        
    Returns:
        dict: The metadata, or an empty dict if not found
    """
    metadata_path = os.path.join(base_dir, session_id, "metadata.json")
    
    if not os.path.exists(metadata_path):
        return {}
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error reading metadata: {str(e)}")
        return {}

def log_metadata_change(session_id, field_name, old_value, new_value, base_dir="outputs"):
    """
    Log metadata changes for debugging.
    
    Args:
        session_id (str): The session ID
        field_name (str): The name of the field that changed
        old_value: The old value of the field
        new_value: The new value of the field
        base_dir (str): Base directory for outputs
    """
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    log_path = os.path.join(session_dir, "metadata_log.txt")
    
    timestamp = datetime.now().isoformat()
    log_entry = f"{timestamp} - Field: {field_name}, Old: {old_value}, New: {new_value}\n"
    
    with open(log_path, 'a') as f:
        f.write(log_entry)

def debug_metadata_changes(session_id, base_dir="outputs"):
    """
    Add a debug function to track metadata changes for a specific session.
    This will log all metadata operations to a debug file.
    
    Args:
        session_id (str): The session ID
        base_dir (str): Base directory for outputs
    """
    # Set up logging to a file
    session_dir = os.path.join(base_dir, session_id)
    os.makedirs(session_dir, exist_ok=True)
    debug_log_path = os.path.join(session_dir, "metadata_debug.log")
    
    # Configure logging
    debug_logger = logging.getLogger(f"metadata_debug_{session_id}")
    debug_logger.setLevel(logging.DEBUG)
    
    # Create file handler
    file_handler = logging.FileHandler(debug_log_path)
    file_handler.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    # Add handler to logger
    debug_logger.addHandler(file_handler)
    
    # Log initial message
    debug_logger.info(f"Starting metadata debug logging for session {session_id}")
    
    # Monkey patch the update functions to add debug logging
    original_update_metadata = update_metadata
    original_update_metadata_field = update_metadata_field
    original_update_metadata_section = update_metadata_section
    
    def debug_update_metadata(session_id, updates, base_dir="outputs"):
        debug_logger.info(f"update_metadata called with updates: {updates}")
        # Get current metadata
        current_metadata = get_metadata(session_id, base_dir)
        debug_logger.info(f"Current metadata before update: {current_metadata}")
        # Call original function
        result = original_update_metadata(session_id, updates, base_dir)
        # Get updated metadata
        updated_metadata = get_metadata(session_id, base_dir)
        debug_logger.info(f"Updated metadata after update: {updated_metadata}")
        # Check for changes to preserve_background_music
        if 'preserve_background_music' in current_metadata or 'preserve_background_music' in updated_metadata:
            old_value = current_metadata.get('preserve_background_music')
            new_value = updated_metadata.get('preserve_background_music')
            if old_value != new_value:
                debug_logger.warning(f"preserve_background_music changed from {old_value} to {new_value}")
        return result
    
    def debug_update_metadata_field(session_id, field_name, field_value, base_dir="outputs"):
        debug_logger.info(f"update_metadata_field called with field: {field_name}, value: {field_value}")
        # Get current metadata
        current_metadata = get_metadata(session_id, base_dir)
        debug_logger.info(f"Current metadata before update: {current_metadata}")
        # Call original function
        result = original_update_metadata_field(session_id, field_name, field_value, base_dir)
        # Get updated metadata
        updated_metadata = get_metadata(session_id, base_dir)
        debug_logger.info(f"Updated metadata after update: {updated_metadata}")
        # Check for changes to preserve_background_music
        if field_name == 'preserve_background_music' or 'preserve_background_music' in current_metadata or 'preserve_background_music' in updated_metadata:
            old_value = current_metadata.get('preserve_background_music')
            new_value = updated_metadata.get('preserve_background_music')
            if old_value != new_value:
                debug_logger.warning(f"preserve_background_music changed from {old_value} to {new_value}")
        return result
    
    def debug_update_metadata_section(session_id, section_name, section_data, base_dir="outputs"):
        debug_logger.info(f"update_metadata_section called with section: {section_name}, data: {section_data}")
        # Get current metadata
        current_metadata = get_metadata(session_id, base_dir)
        debug_logger.info(f"Current metadata before update: {current_metadata}")
        # Call original function
        result = original_update_metadata_section(session_id, section_name, section_data, base_dir)
        # Get updated metadata
        updated_metadata = get_metadata(session_id, base_dir)
        debug_logger.info(f"Updated metadata after update: {updated_metadata}")
        # Check for changes to preserve_background_music
        if 'preserve_background_music' in current_metadata or 'preserve_background_music' in updated_metadata:
            old_value = current_metadata.get('preserve_background_music')
            new_value = updated_metadata.get('preserve_background_music')
            if old_value != new_value:
                debug_logger.warning(f"preserve_background_music changed from {old_value} to {new_value}")
        return result
    
    # Replace the original functions with the debug versions
    globals()['update_metadata'] = debug_update_metadata
    globals()['update_metadata_field'] = debug_update_metadata_field
    globals()['update_metadata_section'] = debug_update_metadata_section
    
    return debug_logger
