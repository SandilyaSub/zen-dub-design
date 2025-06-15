import React, { createContext, useContext, useState, ReactNode } from 'react';

interface AudioData {
  file: File | null;
  url: string | null;
  fileName: string | null;
  duration: number | null;
}

interface TranscriptionData {
  segments: Array<{
    id: string;
    speaker: string;
    start: number;
    end: number;
    text: string;
  }>;
  detectedLanguage: string;
  confidence: number;
}

interface TranslationData {
  provider: 'google' | 'openai' | 'llama' | 'claude' | 'sarvam';
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
}

interface SynthesisData {
  audioUrl: string | null;
  speakerMappings: Record<string, {
    name: string;
    gender: 'Male' | 'Female';
    voiceId: string;
  }>;
  synthesizedAt: string;
}

interface ValidationData {
  semanticSimilarity: number;
  transcriptionAccuracy: number;
  translationQuality: number;
  audioQuality: number;
  overallScore: number;
}

interface SessionContextType {
  sessionId: string;
  audioData: AudioData;
  transcriptionData: TranscriptionData | null;
  translationData: TranslationData | null;
  synthesisData: SynthesisData | null;
  validationData: ValidationData | null;
  currentStep: 'input' | 'transcription' | 'translation' | 'synthesis' | 'validation';
  setAudioData: (data: Partial<AudioData>) => void;
  setTranscriptionData: (data: TranscriptionData) => void;
  setTranslationData: (data: TranslationData) => void;
  setSynthesisData: (data: SynthesisData) => void;
  setValidationData: (data: ValidationData) => void;
  setCurrentStep: (step: SessionContextType['currentStep']) => void;
  resetSession: () => void;
}

const SessionContext = createContext<SessionContextType | undefined>(undefined);

export const useSession = () => {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
};

const SessionProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [sessionId] = useState(() => Date.now().toString());
  const [currentStep, setCurrentStep] = useState<SessionContextType['currentStep']>('input');
  
  const [audioData, setAudioDataState] = useState<AudioData>({
    file: null,
    url: null,
    fileName: null,
    duration: null,
  });

  const [transcriptionData, setTranscriptionData] = useState<TranscriptionData | null>(null);
  const [translationData, setTranslationData] = useState<TranslationData | null>(null);
  const [synthesisData, setSynthesisData] = useState<SynthesisData | null>(null);
  const [validationData, setValidationData] = useState<ValidationData | null>(null);

  const setAudioData = (data: Partial<AudioData>) => {
    setAudioDataState(prev => ({ ...prev, ...data }));
  };

  const resetSession = () => {
    setCurrentStep('input');
    setAudioDataState({
      file: null,
      url: null,
      fileName: null,
      duration: null,
    });
    setTranscriptionData(null);
    setTranslationData(null);
    setSynthesisData(null);
    setValidationData(null);
  };

  return (
    <SessionContext.Provider value={{
      sessionId,
      audioData,
      transcriptionData,
      translationData,
      synthesisData,
      validationData,
      currentStep,
      setAudioData,
      setTranscriptionData,
      setTranslationData,
      setSynthesisData,
      setValidationData,
      setCurrentStep,
      resetSession,
    }}>
      {children}
    </SessionContext.Provider>
  );
};

export default SessionProvider;
