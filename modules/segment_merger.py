"""
Segment merger module for optimizing speech segments.

This module provides functionality to merge consecutive speech segments
from the same speaker when the silence between them is below a threshold.
"""

import logging

# Set up logger
logger = logging.getLogger(__name__)

def merge_segments(segments, max_silence_ms=500):
    """
    Merge consecutive segments from the same speaker if the silence between them
    is less than the specified threshold.
    
    Args:
        segments (list): List of diarization segments
        max_silence_ms (int): Maximum silence duration in milliseconds to merge segments
        
    Returns:
        list: List of merged segments
    """
    if not segments:
        logger.warning("No segments provided for merging")
        return []
        
    # Sort segments by start time to ensure proper ordering
    sorted_segments = sorted(segments, key=lambda x: x.get('start_time', 0))
    logger.info(f"Processing {len(sorted_segments)} segments for merging (max silence: {max_silence_ms}ms)")
    
    merged_segments = []
    current_merged = dict(sorted_segments[0])  # Copy first segment as starting point
    # Calculate duration for the first segment
    current_merged['duration'] = current_merged.get('end_time', 0) - current_merged.get('start_time', 0)
    current_merged['original_segments'] = [dict(sorted_segments[0])]
    
    for segment in sorted_segments[1:]:
        # Calculate silence duration between segments in milliseconds
        silence_duration_ms = (segment.get('start_time', 0) - current_merged.get('end_time', 0)) * 1000
        
        # Check if segments can be merged (same speaker, silence below threshold)
        if (segment.get('speaker') == current_merged.get('speaker') and 
            silence_duration_ms <= max_silence_ms):
            
            logger.debug(f"Merging segment {segment.get('segment_id')} with {current_merged.get('segment_id')} " +
                        f"(silence: {silence_duration_ms:.1f}ms)")
            
            # Update end time and duration
            current_merged['end_time'] = segment.get('end_time', 0)
            current_merged['duration'] = current_merged['end_time'] - current_merged['start_time']
            
            # Concatenate text fields with proper spacing
            current_merged['text'] = (current_merged.get('text', '') + ' ' + 
                                     segment.get('text', '')).strip()
            
            # Handle translated text if present
            if 'translated_text' in segment or 'translated_text' in current_merged:
                current_merged['translated_text'] = (current_merged.get('translated_text', '') + ' ' + 
                                                   segment.get('translated_text', '')).strip()
            
            # Track original segments
            current_merged['original_segments'].append(dict(segment))
        else:
            # Can't merge, save current merged segment and start a new one
            if silence_duration_ms > max_silence_ms:
                logger.debug(f"Cannot merge: silence too long ({silence_duration_ms:.1f}ms)")
            else:
                logger.debug(f"Cannot merge: different speakers ({current_merged.get('speaker')} vs {segment.get('speaker')})")
                
            merged_segments.append(current_merged)
            current_merged = dict(segment)
            # Calculate duration for the new segment
            current_merged['duration'] = current_merged.get('end_time', 0) - current_merged.get('start_time', 0)
            current_merged['original_segments'] = [dict(segment)]
    
    # Add the last merged segment
    merged_segments.append(current_merged)
    
    # Assign new segment IDs
    for i, segment in enumerate(merged_segments):
        segment['segment_id'] = f"merged_{i:03d}"
    
    logger.info(f"Merged {len(segments)} original segments into {len(merged_segments)} segments " +
               f"({len(segments) - len(merged_segments)} segments eliminated)")
    
    return merged_segments
