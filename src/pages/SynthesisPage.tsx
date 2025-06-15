
import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  TextField,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  VolumeUp,
  PlayArrow,
  Download,
  Person
} from '@mui/icons-material';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const VOICE_OPTIONS = [
  { id: 'meera', name: 'Meera', gender: 'Female' },
  { id: 'arvind', name: 'Arvind', gender: 'Male' },
  { id: 'anushka', name: 'Anushka', gender: 'Female' },
  { id: 'karun', name: 'Karun', gender: 'Male' },
  { id: 'priya', name: 'Priya', gender: 'Female' },
  { id: 'rajesh', name: 'Rajesh', gender: 'Male' }
];

const SynthesisPage = () => {
  const { translationData, setSynthesisData } = useSession();
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesisComplete, setSynthesisComplete] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Extract unique speakers from translation data
  const uniqueSpeakers = translationData ? 
    Array.from(new Set(translationData.translatedSegments.map(segment => segment.speaker))) : [];

  // Speaker mapping state
  const [speakerMappings, setSpeakerMappings] = useState<Record<string, {
    name: string;
    gender: 'Male' | 'Female';
    voiceId: string;
  }>>(() => {
    // Initialize with default mappings
    const mappings: Record<string, { name: string; gender: 'Male' | 'Female'; voiceId: string; }> = {};
    uniqueSpeakers.forEach((speaker, index) => {
      const defaultVoice = VOICE_OPTIONS[index % VOICE_OPTIONS.length];
      mappings[speaker] = {
        name: speaker,
        gender: defaultVoice.gender as 'Male' | 'Female',
        voiceId: defaultVoice.id
      };
    });
    return mappings;
  });

  const handleSpeakerMappingChange = (
    speaker: string, 
    field: 'name' | 'gender' | 'voiceId', 
    value: string
  ) => {
    setSpeakerMappings(prev => ({
      ...prev,
      [speaker]: {
        ...prev[speaker],
        [field]: value
      }
    }));
  };

  const handleSynthesize = () => {
    if (!translationData) return;
    
    setIsSynthesizing(true);
    
    // Simulate synthesis process
    setTimeout(() => {
      const mockAudioUrl = 'data:audio/wav;base64,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';
      setAudioUrl(mockAudioUrl);
      
      setSynthesisData({
        provider: 'sarvam',
        voice: 'multi-speaker',
        audioUrl: mockAudioUrl,
        options: {
          pitch: 0,
          pace: 1.0,
          loudness: 1.0
        }
      });
      
      setIsSynthesizing(false);
      setSynthesisComplete(true);
    }, 4000);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <ProgressSteps />
      
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
          Speech Synthesis
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Generate natural speech with speaker mapping
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 4, flexDirection: { xs: 'column', md: 'row' } }}>
        <Box sx={{ flex: 1 }}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Speaker Voice Mapping
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Configure voice settings for each detected speaker
              </Typography>

              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Speaker</strong></TableCell>
                      <TableCell><strong>Name</strong></TableCell>
                      <TableCell><strong>Gender</strong></TableCell>
                      <TableCell><strong>Voice</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {uniqueSpeakers.map((speaker) => (
                      <TableRow key={speaker}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Person fontSize="small" />
                            {speaker}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <TextField
                            size="small"
                            value={speakerMappings[speaker]?.name || speaker}
                            onChange={(e) => handleSpeakerMappingChange(speaker, 'name', e.target.value)}
                            sx={{ minWidth: 120 }}
                          />
                        </TableCell>
                        <TableCell>
                          <FormControl size="small" sx={{ minWidth: 100 }}>
                            <Select
                              value={speakerMappings[speaker]?.gender || 'Female'}
                              onChange={(e) => handleSpeakerMappingChange(speaker, 'gender', e.target.value)}
                            >
                              <MenuItem value="Male">Male</MenuItem>
                              <MenuItem value="Female">Female</MenuItem>
                            </Select>
                          </FormControl>
                        </TableCell>
                        <TableCell>
                          <FormControl size="small" sx={{ minWidth: 120 }}>
                            <Select
                              value={speakerMappings[speaker]?.voiceId || 'meera'}
                              onChange={(e) => handleSpeakerMappingChange(speaker, 'voiceId', e.target.value)}
                            >
                              {VOICE_OPTIONS
                                .filter(voice => voice.gender === (speakerMappings[speaker]?.gender || 'Female'))
                                .map((voice) => (
                                <MenuItem key={voice.id} value={voice.id}>
                                  {voice.name}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Button
                variant="contained"
                onClick={handleSynthesize}
                disabled={isSynthesizing || !translationData || uniqueSpeakers.length === 0}
                fullWidth
                size="large"
                startIcon={<VolumeUp />}
                sx={{ mt: 3 }}
              >
                {isSynthesizing ? 'Generating Speech...' : 'Generate Speech'}
              </Button>
            </CardContent>
          </Card>

          {synthesisComplete && audioUrl && (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Synthesized Audio
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                  <audio 
                    controls 
                    style={{ width: '100%' }}
                    src={audioUrl}
                  >
                    Your browser does not support the audio element.
                  </audio>
                </Box>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<PlayArrow />}
                    fullWidth
                    onClick={() => {
                      const audio = document.querySelector('audio') as HTMLAudioElement;
                      if (audio) {
                        audio.currentTime = 0;
                        audio.play();
                      }
                    }}
                  >
                    Replay Audio
                  </Button>
                  
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    fullWidth
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = audioUrl;
                      link.download = 'synthesized_speech.wav';
                      link.click();
                    }}
                  >
                    Download Audio
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </Box>

        <Box sx={{ flex: 2 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Synthesis Progress
              </Typography>

              {isSynthesizing && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Generating speech with Sarvam AI...
                  </Typography>
                  <LinearProgress />
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Processing {uniqueSpeakers.length} speaker(s)
                  </Typography>
                </Box>
              )}

              {translationData && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Text to Synthesize
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {translationData.translatedSegments.length} segments will be synthesized
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 400, overflowY: 'auto' }}>
                    {translationData.translatedSegments.map((segment) => (
                      <Paper key={segment.id} sx={{ p: 2, backgroundColor: '#f8fafc' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500, mr: 1 }}>
                            {speakerMappings[segment.speaker]?.name || segment.speaker}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ({speakerMappings[segment.speaker]?.gender || 'Female'} - {
                              VOICE_OPTIONS.find(v => v.id === speakerMappings[segment.speaker]?.voiceId)?.name || 'Meera'
                            })
                          </Typography>
                        </Box>
                        <Typography variant="body1">
                          {segment.translatedText}
                        </Typography>
                      </Paper>
                    ))}
                  </Box>
                </Box>
              )}

              {synthesisComplete && (
                <Box sx={{ mt: 3, p: 3, backgroundColor: '#f0fdf4', borderRadius: 2 }}>
                  <Typography variant="h6" sx={{ color: '#059669', mb: 2 }}>
                    Synthesis Complete!
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Multi-speaker audio has been generated successfully with voice mappings applied.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Container>
  );
};

export default SynthesisPage;
