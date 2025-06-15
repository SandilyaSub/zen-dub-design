
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api' 
  : 'http://localhost:5000/api';

export interface TranscriptionSegment {
  id: string;
  speaker: string;
  start: number;
  end: number;
  text: string;
}

export interface TranscriptionResponse {
  success: boolean;
  sessionId: string;
  transcription: string;
  language: string;
  segments: TranscriptionSegment[];
  speakers: Record<string, { id: string; gender: string }>;
  error?: string;
}

export interface TranslationResponse {
  success: boolean;
  sessionId: string;
  sourceLanguage: string;
  targetLanguage: string;
  translatedSegments: Array<{
    id: string;
    originalText: string;
    translatedText: string;
    speaker: string;
  }>;
  metrics?: {
    bertScore: number;
    bleuScore: number;
    wordPreservation: number;
    compositeScore: number;
  };
  error?: string;
}

export interface SynthesisResponse {
  success: boolean;
  sessionId: string;
  audioUrl: string;
  speakerMappings: Record<string, {
    name: string;
    gender: 'Male' | 'Female';
    voiceId: string;
  }>;
  error?: string;
}

class ApiService {
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  async uploadAudio(file: File, sessionId: string): Promise<{ success: boolean; fileName: string; duration: number; error?: string }> {
    const formData = new FormData();
    formData.append('audio', file);
    formData.append('session_id', sessionId);

    try {
      const response = await fetch(`${API_BASE_URL}/upload-audio`, {
        method: 'POST',
        body: formData,
      });

      return await response.json();
    } catch (error) {
      console.error('Audio upload failed:', error);
      return { success: false, fileName: '', duration: 0, error: 'Upload failed' };
    }
  }

  async processVideoUrl(url: string, sessionId: string): Promise<{ success: boolean; fileName: string; duration: number; error?: string }> {
    return this.makeRequest('/process-video-url', {
      method: 'POST',
      body: JSON.stringify({ url, session_id: sessionId }),
    });
  }

  async transcribeAudio(sessionId: string): Promise<TranscriptionResponse> {
    return this.makeRequest(`/transcribe/${sessionId}`, {
      method: 'POST',
    });
  }

  async translateSegments(
    sessionId: string, 
    targetLanguage: string, 
    provider: 'google' | 'openai' | 'llama' | 'claude' | 'sarvam' = 'sarvam'
  ): Promise<TranslationResponse> {
    return this.makeRequest('/translate', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        target_language: targetLanguage,
        provider,
      }),
    });
  }

  async synthesizeSpeech(
    sessionId: string,
    targetLanguage: string,
    provider: 'sarvam' | 'cartesia' = 'sarvam',
    voiceId?: string
  ): Promise<SynthesisResponse> {
    return this.makeRequest('/synthesize-time-aligned', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        target_language: targetLanguage,
        provider,
        voice_id: voiceId,
        options: {
          bit_rate: 128000,
          sample_rate: 44100,
        },
      }),
    });
  }

  async validateOutput(sessionId: string): Promise<{
    success: boolean;
    validation: {
      semanticSimilarity: number;
      transcriptionAccuracy: number;
      translationQuality: number;
      audioQuality: number;
      overallScore: number;
    };
    error?: string;
  }> {
    return this.makeRequest(`/validate/${sessionId}`, {
      method: 'POST',
    });
  }

  async getAvailableVoices(language?: string): Promise<{
    success: boolean;
    voices: Record<string, Array<{
      provider: string;
      id: string;
      name: string;
      gender: string;
    }>>;
    error?: string;
  }> {
    const query = language ? `?language=${language}` : '';
    return this.makeRequest(`/voices${query}`);
  }
}

export const apiService = new ApiService();
