
import { useState, useEffect } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Paper,
  TextField,
  LinearProgress,
  Chip
} from '@mui/material';
import { 
  CheckCircle, 
  VolumeUp, 
  Person,
  Edit,
  ArrowForward
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const TranscriptionPage = () => {
  const navigate = useNavigate();
  const { setTranscriptionData, setCurrentStep } = useSession();
  const [processingComplete, setProcessingComplete] = useState(false);

  const [mockTranscriptionData] = useState({
    detectedLanguage: 'Hindi',
    speakersFound: 2,
    confidence: 0.95,
    segments: [
      {
        id: '1',
        speaker: 'Speaker 1',
        start: 0.0,
        end: 3.2,
        text: 'नमस्ते, आज हम बात करेंगे भारतीय भाषाओं के बारे में।',
        isEditing: false
      },
      {
        id: '2', 
        speaker: 'Speaker 2',
        start: 3.5,
        end: 7.1,
        text: 'जी हाँ, यह बहुत दिलचस्प विषय है। भारत में कितनी भाषाएं बोली जाती हैं?',
        isEditing: false
      },
      {
        id: '3',
        speaker: 'Speaker 1', 
        start: 7.5,
        end: 12.8,
        text: 'भारत में लगभग 700 से अधिक भाषाएं बोली जाती हैं, जिनमें से 22 आधिकारिक भाषाएं हैं।',
        isEditing: false
      }
    ]
  });

  const [segments, setSegments] = useState(mockTranscriptionData.segments);

  useEffect(() => {
    // Simulate processing
    setTimeout(() => {
      setProcessingComplete(true);
    }, 3000);
  }, []);

  const handleEditSegment = (id: string) => {
    setSegments(segments => 
      segments.map(seg => 
        seg.id === id ? { ...seg, isEditing: !seg.isEditing } : seg
      )
    );
  };

  const handleTextChange = (id: string, newText: string) => {
    setSegments(segments => 
      segments.map(seg => 
        seg.id === id ? { ...seg, text: newText } : seg
      )
    );
  };

  const handleContinue = () => {
    setTranscriptionData({
      detectedLanguage: mockTranscriptionData.detectedLanguage,
      confidence: mockTranscriptionData.confidence,
      segments: segments.map(seg => ({ 
        id: seg.id,
        speaker: seg.speaker,
        start: seg.start,
        end: seg.end,
        text: seg.text
      }))
    });
    setCurrentStep('translation');
    navigate('/translation');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${mins}:${secs.padStart(4, '0')}`;
  };

  return (
    <Box sx={{ minHeight: 'calc(100vh - 120px)', backgroundColor: '#f8fafc' }}>
      <Container maxWidth="lg" sx={{ py: 0 }}>
        <ProgressSteps />
        
        <Box sx={{ textAlign: 'center', mb: 4, px: 2 }}>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2, color: '#1f2937' }}>
            Speech Recognition & Diarization
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ fontSize: '1.125rem' }}>
            Automatic transcription with speaker identification
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 4, mb: 4 }}>
          {/* Processing Status */}
          <Box sx={{ flex: 1 }}>
            <Card sx={{ mb: 3 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                  Processing Status
                </Typography>
                
                {processingComplete ? (
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <CheckCircle sx={{ color: '#10b981' }} />
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        Processing Complete
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                        <strong>Detected Language:</strong> {mockTranscriptionData.detectedLanguage}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Speakers Found:</strong> {mockTranscriptionData.speakersFound}
                      </Typography>
                    </Box>
                  </Box>
                ) : (
                  <Box>
                    <LinearProgress sx={{ mb: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                      Processing audio file...
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>

            {processingComplete && (
              <Card>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                    Audio File
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <VolumeUp sx={{ color: '#6366f1' }} />
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      sample_audio.mp3
                    </Typography>
                  </Box>
                  <Button variant="outlined" size="small" startIcon={<VolumeUp />}>
                    Play Audio
                  </Button>
                  <Box sx={{ mt: 3 }}>
                    <Button
                      variant="contained"
                      onClick={handleContinue}
                      size="large"
                      endIcon={<ArrowForward />}
                      fullWidth
                    >
                      Continue to Translation
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            )}
          </Box>

          {/* Transcription Results */}
          <Box sx={{ flex: 2 }}>
            {processingComplete && (
              <Card>
                <CardContent sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                    Transcription Results
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                    {segments.map((segment, index) => (
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
                        <Chip
                          label={`#${index + 1}`}
                          size="small"
                          sx={{
                            position: 'absolute',
                            top: -8,
                            left: 16,
                            backgroundColor: '#6366f1',
                            color: 'white',
                            fontWeight: 600
                          }}
                        />

                        {/* Timing badge */}
                        <Chip
                          label={`${formatTime(segment.start)}-${formatTime(segment.end)}`}
                          size="small"
                          sx={{
                            position: 'absolute',
                            top: -8,
                            right: 16,
                            backgroundColor: '#10b981',
                            color: 'white',
                            fontWeight: 600
                          }}
                        />
                        
                        <Box sx={{ mt: 2 }}>
                          {/* Speaker info */}
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Person sx={{ fontSize: 20, color: '#6b7280' }} />
                              <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
                                {segment.speaker}
                              </Typography>
                            </Box>
                            <Button
                              size="small"
                              onClick={() => handleEditSegment(segment.id)}
                              startIcon={<Edit />}
                              sx={{ minWidth: 'auto' }}
                            >
                              {segment.isEditing ? 'Save' : 'Edit'}
                            </Button>
                          </Box>

                          {/* Transcription text */}
                          {segment.isEditing ? (
                            <TextField
                              fullWidth
                              multiline
                              minRows={2}
                              value={segment.text}
                              onChange={(e) => handleTextChange(segment.id, e.target.value)}
                              variant="outlined"
                              sx={{ 
                                '& .MuiOutlinedInput-root': {
                                  fontSize: '1rem',
                                  lineHeight: 1.6
                                }
                              }}
                            />
                          ) : (
                            <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                              {segment.text}
                            </Typography>
                          )}
                          
                          {/* Play segment button */}
                          <Box sx={{ mt: 2 }}>
                            <Button size="small" startIcon={<VolumeUp />} variant="outlined">
                              Play Segment
                            </Button>
                          </Box>
                        </Box>
                      </Paper>
                    ))}
                  </Box>
                </CardContent>
              </Card>
            )}
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default TranscriptionPage;
