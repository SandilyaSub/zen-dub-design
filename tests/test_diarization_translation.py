import os
import json
import unittest
from modules.google_translation import translate_text
from utils.file_utils import save_diarization_data

class TestDiarizationTranslation(unittest.TestCase):
    def setUp(self):
        # Get the absolute path to the project directory
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.session_id = "session_133scdv8j7fd"
        self.input_file = os.path.join(project_dir, "outputs", self.session_id, "diarization.json")
        self.output_file = os.path.join(project_dir, "outputs", self.session_id, "diarization_translated.json")
        
    def test_diarization_translation(self):
        """
        Test the diarization and translation pipeline:
        1. Load diarization data
        2. Translate each segment
        3. Save translated data with proper structure
        """
        try:
            # Verify input file exists
            if not os.path.exists(self.input_file):
                self.fail(f"Input file not found: {self.input_file}")
            
            # Load diarization data
            with open(self.input_file, 'r', encoding='utf-8') as f:
                diarization_data = json.load(f)
            
            # Get segments
            segments = diarization_data.get("segments", [])
            
            # Translate each segment
            translated_segments = {}
            for i, segment in enumerate(segments):
                # Get the text to translate
                text = segment.get("text", "")
                
                # Translate using Google Translation
                translated_text = translate_text(
                    text=text,
                    source_lang="hi",
                    target_lang="en"
                )
                
                # Store translation
                translated_segments[i] = translated_text
                
                # Add gender information to segment
                segment["gender"] = "M"  # Since we're using the same speaker
            
            # Ensure output directory exists
            output_dir = os.path.dirname(self.output_file)
            os.makedirs(output_dir, exist_ok=True)
            
            # Save translated data
            save_diarization_data(
                output_dir=output_dir,
                transcript=diarization_data.get("transcript", ""),
                segments=segments,
                translated_segments=translated_segments
            )
            
            # Verify output file exists
            if not os.path.exists(self.output_file):
                # Check if any files were created in the directory
                files_in_dir = os.listdir(output_dir)
                print(f"Files in output directory: {files_in_dir}")
                self.fail(f"Output file not created: {self.output_file}")
            
            # Load and verify translated data
            with open(self.output_file, 'r', encoding='utf-8') as f:
                translated_data = json.load(f)
                
            # Verify structure
            self.assertIn("transcript", translated_data)
            self.assertIn("segments", translated_data)
            
            # Verify segments have translations and gender
            for segment in translated_data["segments"]:
                self.assertIn("translated_text", segment)
                self.assertIn("gender", segment)
                self.assertEqual(segment["gender"], "M")
                
            print("\nTest completed successfully!")
            print(f"Translated data saved to: {self.output_file}")
            print(f"\nOriginal transcript:")
            print(diarization_data["transcript"])
            print(f"\nTranslated transcript:")
            print(translated_data["transcript"])
            
        except Exception as e:
            self.fail(f"Test failed with error: {str(e)}")

if __name__ == '__main__':
    unittest.main()
