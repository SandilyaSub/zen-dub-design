import os
import soundfile as sf
import librosa
import numpy as np
from pydub import AudioSegment

# Define a constant to indicate we're in a server environment
SOUNDDEVICE_AVAILABLE = False

def load_audio(file_path):
    """Load audio file and return audio data and sample rate."""
    try:
        audio, sr = librosa.load(file_path, sr=None)
        return audio, sr
    except Exception as e:
        print(f"Error loading audio file: {e}")
        return None, None

def save_audio(audio_data, sample_rate, file_path):
    """Save audio data to file."""
    try:
        sf.write(file_path, audio_data, sample_rate)
        return True
    except Exception as e:
        print(f"Error saving audio file: {e}")
        return False

def record_audio(file_path, duration=10, sample_rate=16000):
    """Record audio from microphone."""
    if not SOUNDDEVICE_AVAILABLE:
        raise RuntimeError("Cannot record audio: sounddevice is not available in this environment. This function can only be used in local development.")
        
    try:
        print(f"Recording audio for {duration} seconds...")
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1)
        sd.wait()  # Wait until recording is finished
        audio_data = audio_data.flatten()  # Convert to mono
        
        # Save the recorded audio
        save_audio(audio_data, sample_rate, file_path)
        print(f"Audio saved to {file_path}")
        return True
    except Exception as e:
        print(f"Error recording audio: {e}")
        return False

def convert_audio_format(input_path, output_path, format='wav'):
    """Convert audio file to specified format."""
    try:
        audio = AudioSegment.from_file(input_path)
        audio.export(output_path, format=format)
        return True
    except Exception as e:
        print(f"Error converting audio format: {e}")
        return False

def split_audio_by_silence(file_path, min_silence_len=500, silence_thresh=-40):
    """Split audio file by silence and return chunks."""
    try:
        audio = AudioSegment.from_file(file_path)
        chunks = librosa.effects.split(
            np.array(audio.get_array_of_samples()),
            top_db=abs(silence_thresh),
            frame_length=int(min_silence_len * audio.frame_rate / 1000)
        )
        
        return chunks, audio.frame_rate
    except Exception as e:
        print(f"Error splitting audio: {e}")
        return [], None

def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds."""
    try:
        audio, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=audio, sr=sr)
        return duration
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return None
