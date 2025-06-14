from modules.tts_processor import TTSProcessor
import json
import os

# Set up the session directory
session_dir = '/Users/sandilya/CascadeProjects/Indic-Translator/outputs/session_3qy1g3fsyuu'
processor = TTSProcessor(output_dir=session_dir)

# Load the segments from the synthesis details file
synthesis_file = os.path.join(session_dir, 'synthesis', 'synthesis_details_None.json')
if os.path.exists(synthesis_file):
    print('Loading synthesis file:', synthesis_file)
    with open(synthesis_file, 'r') as f:
        synthesis_data = json.load(f)
        
    # Set the segments in the processor
    processor.segments = synthesis_data.get('segments', [])
    processor.language = synthesis_data.get('language', 'hindi')
    
    # Process bundles
    bundles = processor.process_pre_silence_speech_bundles()
    print(f'Generated {len(bundles)} bundles')
    
    # Print bundle details
    if bundles:
        for i, bundle in enumerate(bundles):
            print(f"\nBundle {i}:")
            print(f"Original Silence: {bundle['original']['silence_start']} to {bundle['original']['silence_end']}")
            print(f"Original Speech: {bundle['original']['speech_start']} to {bundle['original']['speech_end']}")
            print(f"Translated Silence: {bundle['translated']['silence_start']} to {bundle['translated']['silence_end']}")
            print(f"Translated Speech: {bundle['translated']['speech_start']} to {bundle['translated']['speech_end']}")
else:
    print(f"Synthesis file not found: {synthesis_file}")
