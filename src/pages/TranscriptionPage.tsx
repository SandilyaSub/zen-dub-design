
import { useState, useEffect } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Paper,
  LinearProgress,
  Chip
} from '@mui/material';
import { 
  Transcribe, 
  PlayArrow,
  Pause
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { useProcessingPipeline } from '../hooks/useProcessingPipeline';
import ProgressSteps from '../components/ProgressSteps';

const TranscriptionPage = () => {
  const navigate = useNavigate();
  const { audioData, transcriptionData, setCurrentStep } = useSession();
  const { isProcessing, error, processTranscription } = useProcessingPipeline();
  const [isTranscribing, setIsTranscribing] = useState(false);

  useEffect(() => {
    if (!audioData.fileName) {
      navigate('/');
    }
  }, [audioData.fileName, navigate]);

  const handleStartTranscription = async () => {
    setIsTranscribing(true);
    const success = await processTranscription();
    setIsTranscribing(false);
    
    if (!success) {
      console.error('Transcription failed:', error);
    }
  };

  const handleContinue = () => {
    setCurrentStep('translation');
    navigate('/translation');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  const isProcessingOrTranscribing = isProcessing || isTranscribing;

  return (
    <Container maxWidth="md" sx={{ py: 3 }}>
      <ProgressSteps />
      
      <Box sx={{ textAlign: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600, mb: 1 }}>
          Transcription
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Convert your audio to text with speaker identification
        </Typography>
      </Box>

      <Card>
        <CardContent sx={{ p: 3 }}>
          {/* Audio file info */}
          <Box sx={{ mb: 3, p: 2, backgroundColor: '#f8fafc', borderRadius: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Processing file:
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 500 }}>
              {audioData.fileName}
            </Typography>
            {audioData.duration && (
              <Typography variant="body2" color="text.secondary">
                Duration: {Math.floor(audioData.duration / 60)}:{(audioData.duration % 60).toFixed(0).padStart(2, '0')}
              </Typography>
            )}
          </Box>

          {!transcriptionData && !isProcessingOrTranscribing && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Button
                variant="contained"
                onClick={handleStartTranscription}
                size="large"
                startIcon={<Transcribe />}
                sx={{ mb: 3 }}
              >
                Start Transcription
              </Button>
              <Typography variant="body2" color="text.secondary">
                This will process your audio and identify speakers
              </Typography>
            </Box>
          )}

          {isProcessingOrTranscribing && (
            <Box sx={{ mb: 4 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Processing Audio...
              </Typography>
              <Typography variant="body2" sx={{ mb: 2 }}>
                Transcribing with speaker identification using Sarvam AI...
              </Typography>
              <LinearProgress />
              {error && (
                <Typography variant="body2" color="error" sx={{ mt: 2 }}>
                  Error: {error}
                </Typography>
              )}
            </Box>
          )}

          {transcriptionData && (
            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">
                  Transcription Results
                </Typography>
                <Chip 
                  label={`Language: ${transcriptionData.detectedLanguage}`}
                  color="primary"
                  size="small"
                />
              </Box>
              
              <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <Button 
                  variant="contained" 
                  onClick={handleContinue}
                >
                  Continue to Translation
                </Button>
                <Button variant="outlined" size="small">
                  Edit Segments
                </Button>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {transcriptionData.segments.map((segment, index) => (
                  <Paper 
                    key={segment.id} 
                    elevation={1} 
                    sx={{ 
                      p: 3, 
                      border: '1px solid #e5e7eb',
                      position: 'relative',
                      '&:hover': {
                        boxShadow: 2
                      }
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
                      #{index + 1}
                    </Box>

                    {/* Timing badge */}
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
                      {formatTime(segment.start)}-{formatTime(segment.end)}
                    </Box>
                    
                    <Box sx={{ mt: 1 }}>
                      {/* Speaker info */}
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                          {segment.speaker}
                        </Typography>
                      </Box>

                      {/* Transcribed text */}
                      <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                        {segment.text}
                      </Typography>
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

export default TranscriptionPage;
