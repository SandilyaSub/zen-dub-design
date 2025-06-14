# Translation Evaluation Tests

This directory contains test scripts for evaluating different translation models for the Indic-Translator project.

## Sarvam AI Translation Test

The `test_sarvam_translation.py` script evaluates the Sarvam AI translation model by:
1. Translating a diarization.json file from source language to target language
2. Back-translating the result to the source language
3. Calculating BERT, BLEU, and English word preservation scores
4. Outputting metrics and translated files

### Prerequisites

Install the required packages:

```bash
pip install bert-score nltk
```

### Usage

```bash
python test_sarvam_translation.py --input_file <path> --source_language <lang> --target_language <lang>
```

Example:
```bash
python test_sarvam_translation.py --input_file /path/to/diarization.json --source_language english --target_language hindi
```

### Arguments

- `--input_file`: Path to input diarization.json file (required)
- `--source_language`: Source language (required)
- `--target_language`: Target language (required)
- `--output_dir`: Output directory (default: tests/output)

### Output Files

The script generates the following files in the output directory:
- `{input_filename}_sarvam_translated_{timestamp}.json`: Translated diarization data
- `{input_filename}_sarvam_back_translated_{timestamp}.json`: Back-translated diarization data
- `{input_filename}_sarvam_metrics_{timestamp}.json`: Evaluation metrics
- `sarvam_test_{timestamp}.log`: Log file

### Metrics

The script calculates the following metrics:
- **BERT Score**: Semantic similarity between original and back-translated text
- **BLEU Score**: N-gram precision between original and back-translated text
- **English Word Preservation**: Percentage of English words preserved in translation
- **Composite Score**: Weighted combination of the above metrics (40% BERT, 30% BLEU, 30% English preservation)

## Environment Variables

Make sure to set the following environment variable:
- `SARVAM_API_KEY`: Your Sarvam AI API key
