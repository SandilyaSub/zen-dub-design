#!/usr/bin/env python3
import re

# Read the app.py file
with open('/Users/sandilya/CascadeProjects/Indic-Translator/app.py', 'r') as f:
    content = f.read()

# Define the pattern to find the metadata section
pattern = r"update_metadata_section\(\s*session_id=session_id,\s*section_name='validation',\s*section_data=\{\s*'advanced_metrics': True,\s*'bert_overall': validation_result\.get\('metrics', \{\}\)\.get\('bert_overall', 0\),\s*'bleu_overall': validation_result\.get\('metrics', \{\}\)\.get\('bleu_overall', 0\),\s*'enhanced_composite_score': validation_result\.get\('enhanced_composite_score', 0\)\s*\}\s*\)"

# Define the replacement with audio extraction score
replacement = """update_metadata_section(
            session_id=session_id,
            section_name='validation',
            section_data={
                'advanced_metrics': True,
                'bert_overall': validation_result.get('metrics', {}).get('bert_overall', 0),
                'bleu_overall': validation_result.get('metrics', {}).get('bleu_overall', 0),
                'enhanced_composite_score': validation_result.get('enhanced_composite_score', 0),
                'audio_extraction_score': validation_result.get('audio_extraction_score', 0),
                'bert_segment_weighted': validation_result.get('metrics', {}).get('bert_segment_weighted', 0),
                'bleu_segment_weighted': validation_result.get('metrics', {}).get('bleu_segment_weighted', 0)
            }
        )"""

# Replace the pattern with the new content
updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the updated content back to app.py
with open('/Users/sandilya/CascadeProjects/Indic-Translator/app.py', 'w') as f:
    f.write(updated_content)

print("Updated app.py successfully!")
