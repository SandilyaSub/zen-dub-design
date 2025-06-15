
import { useState, useEffect } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  LinearProgress,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Divider
} from '@mui/material';
import { 
  VolumeUp,
  CheckCircle,
  Person,
  PlayArrow
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const TranscriptionPage = () => {
  const navigate = useNavigate();
  const { audioData, setTranscriptionData, setCurrentStep } = useSession();
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [segments, setSegments] = useState<Array<{
    id: string;
    speaker: string;
    start: number;
    end: number;
    text: string;
  }>>([]);

  useEffect(() => {
    if (!audioData.fileName) {
      navigate('/');
      return;
    }
    
    // Start processing automatically
    handleTranscription();
  }, []);

  const handleTranscription = () => {
    setIsProcessing(true);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          
          // Mock transcription results
          setDetectedLanguage('Hindi');
          setSegments([
            {
              id: '1',
              speaker: 'Speaker 1',
              start: 0.0,
              end: 3.2,
              text: 'नमस्ते, आज हम बात करेंगे भारतीय भाषाओं के बारे में।'
            },
            {
              id: '2', 
              speaker: 'Speaker 2',
              start: 3.5,
              end: 7.1,
              text: 'जी हाँ, यह बहुत दिलचस्प विषय है। भारत में कितनी भाषाएं बोली जाती हैं?'
            },
            {
              id: '3',
              speaker: 'Speaker 1', 
              start: 7.4,
              end: 12.8,
              text: 'भारत में लगभग 1600 से अधिक भाषाएं बोली जाती हैं, जिनमें से 22 संविधान में मान्यता प्राप्त हैं।'
            }
          ]);
          
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleSegmentEdit = (id: string, newText: string) => {
    setSegments(segments.map(seg => 
      seg.id === id ? { ...seg, text: newText } : seg
    ));
  };

  const handleSpeakerChange = (id: string, newSpeaker: string) => {
    setSegments(segments.map(seg => 
      seg.id === id ? { ...seg, speaker: newSpeaker } : seg
    ));
  };

  const handleContinue = () => {
    setTranscriptionData({
      segments,
      detectedLanguage,
      confidence: 0.94
    });
    setCurrentStep('transliteration');
    navigate('/transliteration');
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
          Speech Recognition & Diarization
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Automatic transcription with speaker identification
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 4, flexDirection: { xs: 'column', md: 'row' } }}>
        <Box sx={{ flex: 1 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Processing Status
              </Typography>
              
              {isProcessing ? (
                <Box>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    Processing audio: {progress}%
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={progress}
                    sx={{ height: 8, borderRadius: 4, mb: 2 }}
                  />
                  <Typography variant="body2" color="text.secondary">
                    Performing VAD segmentation and speaker diarization...
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <CheckCircle sx={{ color: '#10b981', mr: 1 }} />
                    <Typography variant="body1">
                      Processing Complete
                    </Typography>
                  </Box>
                  
                  <Paper sx={{ p: 2, mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Detected Language:</strong> {detectedLanguage}
                    </Typography>
                    <Typography variant="body2">
                      <strong>Speakers Found:</strong> {new Set(segments.map(s => s.speaker)).size}
                    </Typography>
                  </Paper>
                </Box>
              )}

              <Divider sx={{ my: 2 }} />
              
              <Typography variant="h6" sx={{ mb: 2 }}>
                Audio File
              </Typography>
              <Chip 
                label={audioData.fileName} 
                icon={<VolumeUp />}
                sx={{ mb: 2 }}
              />
              
              <Button
                variant="outlined"
                startIcon={<PlayArrow />}
                fullWidth
                sx={{ mb: 2 }}
              >
                Play Audio
              </Button>

              <Button
                variant="contained" 
                onClick={handleContinue}
                disabled={isProcessing || segments.length === 0}
                fullWidth
                size="large"
              >
                Continue to Transliteration
              </Button>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: 2 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Transcription Results
              </Typography>

              {isProcessing ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary">
                    Processing audio with advanced VAD and speaker diarization...
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {segments.map((segment) => (
                    <Paper 
                      key={segment.id} 
                      elevation={1} 
                      sx={{ p: 3, border: '1px solid #e5e7eb' }}
                    >
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                          <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>Speaker</InputLabel>
                            <Select
                              value={segment.speaker}
                              label="Speaker"
                              onChange={(e) => handleSpeakerChange(segment.id, e.target.value)}
                            >
                              <MenuItem value="Speaker 1">Speaker 1</MenuItem>
                              <MenuItem value="Speaker 2">Speaker 2</MenuItem>
                              <MenuItem value="Speaker 3">Speaker 3</MenuItem>
                            </Select>
                          </FormControl>
                          <Chip 
                            icon={<Person />}
                            label={`${formatTime(segment.start)} - ${formatTime(segment.end)}`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                        <Button
                          size="small"
                          startIcon={<PlayArrow />}
                          variant="outlined"
                        >
                          Play Segment
                        </Button>
                      </Box>
                      
                      <TextField
                        fullWidth
                        multiline
                        minRows={2}
                        value={segment.text}
                        onChange={(e) => handleSegmentEdit(segment.id, e.target.value)}
                        variant="outlined"
                        sx={{ 
                          '& .MuiOutlinedInput-root': {
                            fontSize: '1rem',
                            lineHeight: 1.6
                          }
                        }}
                      />
                    </Paper>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Container>
  );
};

export default TranscriptionPage;
