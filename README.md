# Indic-Translator

A robust, modular speech-to-speech translation system for Indian languages, enabling content creators and users to translate, transcribe, transliterate, and synthesize speech efficiently across multiple Indic languages.

## Overview

Indic-Translator is designed to facilitate seamless speech-to-speech and text-based translation workflows for Indian languages. The system supports audio upload/recording, language detection, transcription, transliteration, translation, and speech synthesis, with advanced session management, error handling, and cost-efficient API usage.

## Features

- **Audio Input**: Upload audio files (.mp3, .wav, etc.) or record via microphone
- **Language Detection**: Automatic detection of spoken language from audio
- **Transcription**: Accurate speech-to-text with speaker diarization and VAD segmentation
- **Transliteration**: Convert Roman script input to Indic scripts using Google Input Tools
- **Translation**: Multi-provider translation system with Google Gemini, OpenAI GPT-4.1, Llama via Together API, Claude, and Sarvam
- **Translation Evaluation**: Advanced metrics including BERT, BLEU, and word preservation for quality assessment
- **Speech Synthesis**: Generate speech in the target language with support for multiple voices
- **Session Management**: Organize and cache files and results per user session
- **Error Handling & Logging**: Robust error messages and logs for all processing steps
- **Caching & Optimization**: Avoid redundant API calls and minimize computational/billing overhead

## Supported Languages

- Hindi
- Telugu
- Tamil
- Kannada
- Gujarati
- Marathi
- Bengali
- Punjabi
- Malayalam
- Odia
- Assamese
- Nepali
- Sanskrit
- Sinhalese
- Urdu
- English (input only)

## Technical Architecture

### Frontend
- HTML5, CSS3, JavaScript
- Responsive design with streamlined workflow
- Direct API integration for transcription, translation, and synthesis

### Backend
- Python 3 (3.8+ recommended)
- Flask web framework
- RESTful API endpoints for each processing step
- Session-based file and data management
- Enhanced CORS and security configuration

### Core Modules
- **Speech Recognition**: Sarvam Speech API, VAD segmentation, diarization
- **Transliteration**: Google Input Tools API, locale-aware language code mapping
- **Translation**: 
  - Multiple LLM providers:
    - Google Generative AI (Gemini 1.5 Flash)
    - OpenAI (GPT-4.1)
    - Llama (via Together API)
    - Claude (via Vertex AI)
    - Sarvam (IndicTrans2)
  - Translation quality metrics:
    - BERT score (semantic similarity)
    - BLEU score (fluency)
    - Word preservation (terminology retention)
    - Composite scoring
- **Speech Synthesis**: Sarvam TTS, OpenVoice, multi-speaker/voice support
- **Utilities**: Audio conversion (ffmpeg), file management, error logging

## Setup Instructions

### Prerequisites
- Python 3.8 or higher (Python 3.13 supported)
- pip (Python package installer)
- ffmpeg installed and available in PATH (see below)
- Virtual environment (recommended)
- Modern web browser

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Indic-Translator.git
cd Indic-Translator
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install core dependencies:
```bash
pip install -r requirements.txt
```

4. Install translation metrics dependencies:
```bash
pip install -r requirements-translation-metrics.txt
```

5. Install LLM provider libraries:
```bash
pip install openai together
```

6. Set up API keys in a `.env` file:
```
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
TOGETHER_API_KEY=your_together_api_key
SARVAM_API_KEY=your_sarvam_api_key
```

7. Ensure ffmpeg is installed and in your PATH:
```bash
# On macOS (Apple Silicon or Intel):
brew install ffmpeg
# Or use your system's package manager
ffmpeg -version
```

8. Run the application:
```bash
flask run
```

9. Open your browser and navigate to:
```
http://localhost:5000
```

## User Journey

1. **Input Stage**:
   - Upload or record audio
   - Select/confirm target language

2. **Transcription Stage**:
   - Automatic language detection
   - View and edit transcription with diarization

3. **Transliteration Stage**:
   - Enter text in Roman script and transliterate to Indic script (if needed)

4. **Translation Stage**:
   - Translate and edit text between Indic languages
   - Option to select translation provider (Google, OpenAI, Llama, etc.)

5. **Synthesis Stage**:
   - Generate and play/download synthesized speech

## Project Structure

```
Indic-Translator/
├── app.py                     # Main Flask application
├── requirements.txt           # Core Python dependencies
├── requirements-translation-metrics.txt  # Translation metrics dependencies
├── modules/                   # Core functionality modules
│   ├── sarvam_speech.py       # Speech recognition, VAD, diarization
│   ├── tts_processor.py       # Text-to-speech synthesis
│   ├── google_translation.py  # Google Gemini translation
│   ├── openai_translation.py  # OpenAI GPT-4.1 translation
│   ├── llama_translation.py   # Llama translation via Together API
│   ├── claude_translation.py  # Claude translation
│   ├── sarvam_translation.py  # Sarvam IndicTrans2 translation
│   ├── translation_metrics.py # BERT, BLEU, and word preservation metrics
│   └── vad_segmentation.py    # VAD segmentation logic
├── utils/                     # Utility functions
│   ├── audio_utils.py         # Audio processing utilities
│   └── file_utils.py          # File handling utilities
├── tests/                     # Test scripts
│   ├── test_openai_translation.py  # Test OpenAI translation
│   ├── test_llama_translation.py   # Test Llama translation
│   └── test_claude_translation.py  # Test Claude translation
├── app/                       # Web application assets
│   ├── static/                # Static files (CSS, JS)
│   └── templates/             # HTML templates
├── uploads/                   # Uploaded audio files (per session)
├── outputs/                   # Generated files (per session)
├── logs/                      # Log files
└── models/                    # Downloaded model files
```

## Translation Module Usage

Each translation module can be used independently for testing or integration:

### Google Gemini Translation

```python
from modules.google_translation import translate_diarized_content

# Translate diarized content
translated_data = translate_diarized_content(
    diarization_data,  # Dictionary with segments
    target_language="english",
    source_language="hindi"
)
```

### OpenAI Translation

```python
from modules.openai_translation import openai_translate_diarized_content

# Translate diarized content
translated_data = openai_translate_diarized_content(
    diarization_data,  # Dictionary with segments
    target_language="english",
    source_language="hindi",
    api_key="your_openai_api_key"  # Optional, falls back to .env
)
```

### Llama Translation (via Together API)

```python
from modules.llama_translation import llama_translate_diarized_content

# Translate diarized content
translated_data = llama_translate_diarized_content(
    diarization_data,  # Dictionary with segments
    target_language="english",
    source_language="hindi",
    api_key="your_together_api_key"  # Optional, falls back to .env
)
```

## Translation Metrics

The system supports comprehensive translation quality evaluation:

```python
from modules.translation_metrics import calculate_all_metrics

# Calculate metrics between original, translated, and back-translated content
metrics = calculate_all_metrics(
    original_data,      # Original diarization data
    translated_data,    # Translated diarization data
    back_translated_data  # Back-translated diarization data
)

# Metrics include:
# - BERT score (overall and per-segment)
# - BLEU score (overall and per-segment)
# - Word preservation (overall and per-segment)
# - Composite score (overall and per-segment)
```

## Troubleshooting

- **ffmpeg not found**: Ensure ffmpeg is installed and in your PATH. See setup instructions above.
- **403 Forbidden on localhost**: Clear browser cookies, ensure no zombie Flask processes, and use a consistent SECRET_KEY.
- **API errors**: Check your `.env` for valid API keys for all providers (Google, OpenAI, Together, Sarvam).
- **File not found**: Ensure uploads and outputs directories exist and have proper permissions.
- **Translation module errors**: Verify API keys and check logs in the `logs/` directory.

## Future Enhancements

- Agentic translation orchestration using multiple LLMs with automatic selection
- Cloud deployment for scalability
- User authentication and profile management
- Batch processing for multiple files
- Advanced voice cloning with emotion preservation
- Support for more Indian languages and dialects
- Integration with social media platforms for direct publishing
- More robust caching and offline support

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [AI4Bharat](https://ai4bharat.org/) for Sarvam Speech and IndicTrans2
- [Google](https://cloud.google.com/) for Input Tools and Generative AI
- [OpenAI](https://openai.com/) for GPT-4.1
- [Together.ai](https://together.ai/) for Llama API access
- [Anthropic](https://anthropic.com/) for Claude
- [MyShell.ai](https://myshell.ai/) for OpenVoice
- All contributors and testers
