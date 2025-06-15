
import { useState } from 'react';
import { useSession } from '../context/SessionContext';
import { apiService } from '../services/apiService';

export const useProcessingPipeline = () => {
  const { 
    sessionId, 
    setTranscriptionData, 
    setTranslationData, 
    setSynthesisData, 
    setValidationData,
    setCurrentStep 
  } = useSession();
  
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const processTranscription = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const result = await apiService.transcribeAudio(sessionId);
      
      if (result.success) {
        setTranscriptionData({
          segments: result.segments,
          detectedLanguage: result.language,
          confidence: 0.85, // Default confidence since backend might not provide it
        });
        setCurrentStep('translation');
        return true;
      } else {
        setError(result.error || 'Transcription failed');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transcription failed');
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  const processTranslation = async (targetLanguage: string, provider: 'google' | 'openai' | 'llama' | 'claude' | 'sarvam' = 'sarvam') => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const result = await apiService.translateSegments(sessionId, targetLanguage, provider);
      
      if (result.success) {
        setTranslationData({
          provider,
          sourceLanguage: result.sourceLanguage,
          targetLanguage: result.targetLanguage,
          translatedSegments: result.translatedSegments,
          metrics: result.metrics,
        });
        setCurrentStep('synthesis');
        return true;
      } else {
        setError(result.error || 'Translation failed');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  const processSynthesis = async (targetLanguage: string, provider: 'sarvam' | 'cartesia' = 'sarvam', voiceId?: string) => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const result = await apiService.synthesizeSpeech(sessionId, targetLanguage, provider, voiceId);
      
      if (result.success) {
        setSynthesisData({
          audioUrl: result.audioUrl,
          speakerMappings: result.speakerMappings,
          synthesizedAt: new Date().toISOString(),
        });
        setCurrentStep('validation');
        return true;
      } else {
        setError(result.error || 'Speech synthesis failed');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Speech synthesis failed');
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  const processValidation = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      const result = await apiService.validateOutput(sessionId);
      
      if (result.success) {
        setValidationData(result.validation);
        return true;
      } else {
        setError(result.error || 'Validation failed');
        return false;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
      return false;
    } finally {
      setIsProcessing(false);
    }
  };

  return {
    isProcessing,
    error,
    processTranscription,
    processTranslation,
    processSynthesis,
    processValidation,
  };
};
