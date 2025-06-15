
import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Paper,
  TextField,
  LinearProgress
} from '@mui/material';
import { 
  Translate
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const TranslationPage = () => {
  const navigate = useNavigate();
  const { transcriptionData, setTranslationData, setCurrentStep } = useSession();
  const [isTranslating, setIsTranslating] = useState(false);
  const [translatedSegments, setTranslatedSegments] = useState<Array<{
    id: string;
    originalText: string;
    translatedText: string;
    speaker: string;
    start: number;
    end: number;
  }>>([]);

  // Get dynamic languages from transcription data or use defaults
  const sourceLanguage = transcriptionData?.detectedLanguage || 'Hindi';
  const targetLanguage = 'Telugu'; // This would come from session/API in real implementation

  const handleTranslate = () => {
    if (!transcriptionData) return;
    
    setIsTranslating(true);
    
    setTimeout(() => {
      // Mock translation results based on transcription segments
      const mockTranslations = transcriptionData.segments.map(segment => ({
        id: segment.id,
        originalText: segment.text,
        translatedText: targetLanguage === 'Telugu' 
          ? `నమస్కారం, ఈరోజు మేము భారతీయ భాషల గురించి మాట్లాడుతాము. ఇది చాలా ఆసక్తికరమైన విషయం. భారతదేశంలో ఎన్ని భాషలు మాట్లాడుతారు?`
          : `Hello, today we will talk about Indian languages. This is very interesting topic. How many languages are spoken in India?`,
        speaker: segment.speaker,
        start: segment.start,
        end: segment.end
      }));
      
      setTranslatedSegments(mockTranslations);
      setIsTranslating(false);
    }, 3000);
  };

  const handleTranslationEdit = (id: string, newTranslation: string) => {
    setTranslatedSegments(segments => 
      segments.map(seg => 
        seg.id === id ? { ...seg, translatedText: newTranslation } : seg
      )
    );
  };

  const handleContinue = () => {
    if (translatedSegments.length > 0) {
      setTranslationData({
        provider: 'sarvam' as any,
        sourceLanguage,
        targetLanguage,
        translatedSegments,
        metrics: {
          bertScore: 0.89,
          bleuScore: 0.76,
          wordPreservation: 0.82,
          compositeScore: 0.83
        }
      });
    }
    setCurrentStep('synthesis');
    navigate('/synthesis');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <ProgressSteps />
      
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
          Translation
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Translation from {sourceLanguage} to {targetLanguage}
        </Typography>
      </Box>

      <Card>
        <CardContent>
          {!isTranslating && translatedSegments.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Button
                variant="contained"
                onClick={handleTranslate}
                disabled={!transcriptionData}
                size="large"
                startIcon={<Translate />}
                sx={{ mb: 3 }}
              >
                Start Translation
              </Button>
              <Typography variant="body2" color="text.secondary">
                Click to begin translating your transcribed segments
              </Typography>
            </Box>
          )}

          {isTranslating && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Translation
              </Typography>
              <TextField
                fullWidth
                multiline
                minRows={4}
                placeholder="Translation will appear here..."
                disabled
                sx={{ mb: 3 }}
              />
              <Typography variant="body2" sx={{ mb: 2 }}>
                Translating with Sarvam AI...
              </Typography>
              <LinearProgress />
              
              <Box sx={{ mt: 4 }}>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Translation Editor
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  Edit individual translation segments below
                </Typography>
                
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                  <Button variant="outlined" size="small" disabled>
                    Save Edits
                  </Button>
                  <Button variant="outlined" size="small" disabled>
                    Save & Continue
                  </Button>
                </Box>
              </Box>
            </Box>
          )}

          {translatedSegments.length > 0 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Translation
              </Typography>
              <TextField
                fullWidth
                multiline
                minRows={4}
                value={translatedSegments.map(seg => seg.translatedText).join(' ')}
                disabled
                sx={{ mb: 4 }}
              />
              
              <Typography variant="h6" sx={{ mb: 2 }}>
                Translation Editor
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Edit individual translation segments below
              </Typography>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Button variant="outlined" size="small">
                  Save Edits
                </Button>
                <Button 
                  variant="contained" 
                  size="small"
                  onClick={handleContinue}
                >
                  Save & Continue
                </Button>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {translatedSegments.map((segment, index) => (
                  <Paper 
                    key={segment.id} 
                    elevation={1} 
                    sx={{ 
                      p: 3, 
                      border: '1px solid #e5e7eb',
                      position: 'relative'
                    }}
                  >
                    {/* Segment number badge */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -8,
                        left: 16,
                        backgroundColor: '#6366f1',
                        color: 'white',
                        borderRadius: '12px',
                        px: 2,
                        py: 0.5,
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        boxShadow: 1
                      }}
                    >
                      #{index + 1} {formatTime(segment.start)}-{formatTime(segment.end)}
                    </Box>

                    {/* Speaker badge */}
                    <Box
                      sx={{
                        position: 'absolute',
                        top: -8,
                        right: 16,
                        backgroundColor: '#10b981',
                        color: 'white',
                        borderRadius: '12px',
                        px: 2,
                        py: 0.5,
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        boxShadow: 1
                      }}
                    >
                      {segment.speaker}
                    </Box>
                    
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
                        Original:
                      </Typography>
                      <Typography 
                        variant="body1" 
                        sx={{ 
                          mb: 3,
                          p: 2,
                          backgroundColor: '#f9fafb',
                          borderRadius: 1,
                          border: '1px solid #e5e7eb'
                        }}
                      >
                        {segment.originalText}
                      </Typography>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
                        Translation:
                      </Typography>
                      <TextField
                        fullWidth
                        multiline
                        minRows={2}
                        value={segment.translatedText}
                        onChange={(e) => handleTranslationEdit(segment.id, e.target.value)}
                        variant="outlined"
                        sx={{ 
                          '& .MuiOutlinedInput-root': {
                            fontSize: '1rem',
                            lineHeight: 1.6
                          }
                        }}
                      />
                    </Box>
                  </Paper>
                ))}
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>
    </Container>
  );
};

export default TranslationPage;
