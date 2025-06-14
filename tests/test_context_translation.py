#!/usr/bin/env python3
"""
Test script for context-enhanced translation module.
"""
import os
import sys
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

# Import the module to test
from modules.google_translation import translate_diarized_content

def main():
    """Test the context-enhanced translation with a sample diarization file."""
    
    # Sample diarization data with context-dependent segments
    sample_data = {
  "transcript": "నాన్న టైం చూసి ఫోన్ తీసి హలో పంతులుగారు బయల్దేరిపోమంటారా? ఒక పావు గంటలో రాహు కాలం అయిపోతుంది. అవ్వగానే బయలుదేరండి మా అబ్బాయి జాతక చక్రము అప్పుడు మీరు రాసిచ్చారు కదండీ. అది ఒక్కటి తీసుకొస్తే సరిపోద్దా? ఇంకేమైనా తెమ్మంటారా? మీ అబ్బాయి చక్రంతో పాటు మీ అబ్బాయిని కూడా తోలుకురండి. వాడెందుకు పంతులుగారు? వాడి జాతకం వాడు విన్నాడంటే బాగుందంటే రెచ్చిపోతాడు బాలేదంటే గింజుకుపోతాడు నేను చక్రంలో ఏమి కనబడలేదు అనుకో వాడి చెయ్యి చూడొద్దా? వాడి చెయ్యిలో ఏమి కనబడలేదనుకో. వాడి కాళ్ళు చూడొద్దా? వాడి కాళ్ళల్లో కూడా ఏ పిండాకుడు కనబడలేదనుకో. అర్థమైందా అండి మీరు ఆయన్ని చూడాలి తీసుకువస్తాను అన్నీ ఫోన్ పెట్టేస్తారు ఎవ్వై",
  "segments": [
    {
      "segment_id": "seg_000",
      "speaker": "SPEAKER_00",
      "text": "నాన్న టైం చూసి ఫోన్ తీసి",
      "start_time": 2.57,
      "end_time": 4.38,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_001",
      "speaker": "SPEAKER_01",
      "text": "హలో పంతులుగారు బయల్దేరిపోమంటారా?",
      "start_time": 5.27,
      "end_time": 7.52,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_002",
      "speaker": "SPEAKER_00",
      "text": "ఒక పావు గంటలో రాహు కాలం అయిపోతుంది.",
      "start_time": 7.59,
      "end_time": 10.05,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_003",
      "speaker": "SPEAKER_01",
      "text": "అవ్వగానే బయలుదేరండి",
      "start_time": 10.122,
      "end_time": 11.432,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_004",
      "speaker": "SPEAKER_00",
      "text": "మా అబ్బాయి జాతక చక్రము అప్పుడు మీరు రాసిచ్చారు కదండీ. అది ఒక్కటి తీసుకొస్తే సరిపోద్దా? ఇంకేమైనా తెమ్మంటారా?",
      "start_time": 11.602,
      "end_time": 16.942,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_005",
      "speaker": "SPEAKER_00",
      "text": "మీ అబ్బాయి చక్రంతో పాటు మీ అబ్బాయిని కూడా తోలుకురండి.",
      "start_time": 17.034000000000002,
      "end_time": 19.964000000000002,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_006",
      "speaker": "SPEAKER_01",
      "text": "వాడెందుకు పంతులుగారు?",
      "start_time": 20.234,
      "end_time": 21.564,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_007",
      "speaker": "SPEAKER_00",
      "text": "వాడి జాతకం వాడు విన్నాడంటే బాగుందంటే రెచ్చిపోతాడు బాలేదంటే గింజుకుపోతాడు",
      "start_time": 21.642000000000003,
      "end_time": 25.932000000000002,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_008",
      "speaker": "SPEAKER_01",
      "text": "నేను చక్రంలో ఏమి కనబడలేదు అనుకో",
      "start_time": 26.002000000000002,
      "end_time": 27.962000000000003,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_009",
      "speaker": "SPEAKER_00",
      "text": "వాడి చెయ్యి చూడొద్దా? వాడి చెయ్యిలో ఏమి కనబడలేదనుకో. వాడి కాళ్ళు చూడొద్దా? వాడి కాళ్ళల్లో కూడా ఏ పిండాకుడు కనబడలేదనుకో.",
      "start_time": 28.106,
      "end_time": 34.846000000000004,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_010",
      "speaker": "SPEAKER_01",
      "text": "అర్థమైందా అండి",
      "start_time": 34.846000000000004,
      "end_time": 35.806,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_011",
      "speaker": "SPEAKER_00",
      "text": "మీరు ఆయన్ని చూడాలి తీసుకువస్తాను",
      "start_time": 35.85,
      "end_time": 37.68000000000001,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_012",
      "speaker": "SPEAKER_01",
      "text": "అన్నీ ఫోన్ పెట్టేస్తారు",
      "start_time": 37.59,
      "end_time": 38.74,
      "gender": "unknown",
      "pace": 1.0
    },
    {
      "segment_id": "seg_013",
      "speaker": "SPEAKER_00",
      "text": "ఎవ్వై",
      "start_time": 38.86000000000001,
      "end_time": 39.13,
      "gender": "unknown",
      "pace": 1.0
    }
  ],
  "language_code": "te-IN"
}
    
    # Translate with context awareness
    print("Translating with context awareness...")
    translated_data = translate_diarized_content(sample_data, "hi", "te")
    
    # Print the results
    print("\nTranslation Results:")
    print("-" * 50)
    
    for segment in translated_data["segments"]:
        print(f"Segment {segment['segment_id']}:")
        print(f"Original: {segment['text']}")
        print(f"Translated: {segment['translated_text']}")
        print("-" * 30)
    
    # Save the results to a file
    output_dir = Path("tests/output")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / "context_translation_result.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    # Verify TTS compatibility
    print("\nVerifying TTS compatibility...")
    tts_segments = []
    for segment in translated_data["segments"]:
        tts_segment = {
            "segment_id": segment["segment_id"],
            "speaker": segment["speaker"],
            "start_time": segment["start_time"],
            "end_time": segment["end_time"],
            "text": segment["translated_text"],
            "translated_text": segment["translated_text"],
            "gender": segment.get("gender", "unknown"),
            "language": "en"  # Target language
        }
        tts_segments.append(tts_segment)
    
    tts_compatible_file = output_dir / "tts_compatible.json"
    with open(tts_compatible_file, "w", encoding="utf-8") as f:
        json.dump({"segments": tts_segments}, f, ensure_ascii=False, indent=2)
    
    print(f"TTS-compatible format saved to {tts_compatible_file}")

if __name__ == "__main__":
    main()
