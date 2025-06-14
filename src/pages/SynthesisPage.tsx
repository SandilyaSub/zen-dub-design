
import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Chip,
  Slider,
  LinearProgress
} from '@mui/material';
import { 
  VolumeUp,
  PlayArrow,
  Download,
  Tune
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';

const TTS_PROVIDERS = [
  { id: 'sarvam', name: 'Sarvam AI', description: 'Natural Indian voices' },
  { id: 'openvoice', name: 'OpenVoice', description: 'Voice cloning technology' }
];

const VOICE_OPTIONS = {
  sarvam: [
    { id: 'meera', name: 'Meera', gender: 'Female' },
    { id: 'arvind', name: 'Arvind', gender: 'Male' },
    { id: 'anushka', name: 'Anushka', gender: 'Female' },
    { id: 'karun', name: 'Karun', gender: 'Male' }
  ],
  openvoice: [
    { id: 'default', name: 'Default Voice', gender: 'Neutral' },
    { id: 'cloned', name: 'Cloned Voice', gender: 'Custom' }
  ]
};

const SynthesisPage = () => {
  const navigate = useNavigate();
  const { translationData, setSynthesisData } = useSession();
  const [selectedProvider, setSelectedProvider] = useState<'sarvam' | 'openvoice'>('sarvam');
  const [selectedVoice, setSelectedVoice] = useState('meera');
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [synthesisComplete, setSynthesisComplete] = useState(false);
  const [voiceOptions, setVoiceOptions] = useState({
    pitch: 0,
    pace: 1.0,
    loudness: 1.0
  });

  const handleSynthesize = () => {
    if (!translationData) return;
    
    setIsSynthesizing(true);
    
    setTimeout(() => {
      setSynthesisData({
        provider: selectedProvider,
        voice: selectedVoice,
        audioUrl: 'mock-audio-url.mp3',
        options: voiceOptions
      });
      
      setIsSynthesizing(false);
      setSynthesisComplete(true);
    }, 4000);
  };

  const handleProviderChange = (provider: 'sarvam' | 'openvoice') => {
    setSelectedProvider(provider);
    setSelectedVoice(VOICE_OPTIONS[provider][0].id);
  };

  const availableVoices = VOICE_OPTIONS[selectedProvider] || [];

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
          Speech Synthesis
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Generate natural speech with advanced TTS technology
        </Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                TTS Provider
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Provider</InputLabel>
                <Select
                  value={selectedProvider}
                  label="Provider"
                  onChange={(e) => handleProviderChange(e.target.value as 'sarvam' | 'openvoice')}
                >
                  {TTS_PROVIDERS.map((provider) => (
                    <MenuItem key={provider.id} value={provider.id}>
                      {provider.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Voice</InputLabel>
                <Select
                  value={selectedVoice}
                  label="Voice"
                  onChange={(e) => setSelectedVoice(e.target.value)}
                >
                  {availableVoices.map((voice) => (
                    <MenuItem key={voice.id} value={voice.id}>
                      {voice.name} ({voice.gender})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Typography variant="h6" sx={{ mb: 2 }}>
                Voice Settings
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Pitch: {voiceOptions.pitch}
                </Typography>
                <Slider
                  value={voiceOptions.pitch}
                  onChange={(_, value) => setVoiceOptions({...voiceOptions, pitch: value as number})}
                  min={-0.75}
                  max={0.75}
                  step={0.25}
                  marks
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Pace: {voiceOptions.pace}x
                </Typography>
                <Slider
                  value={voiceOptions.pace}
                  onChange={(_, value) => setVoiceOptions({...voiceOptions, pace: value as number})}
                  min={0.5}
                  max={2.0}
                  step={0.1}
                  marks
                />
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" sx={{ mb: 1 }}>
                  Loudness: {voiceOptions.loudness}x
                </Typography>
                <Slider
                  value={voiceOptions.loudness}
                  onChange={(_, value) => setVoiceOptions({...voiceOptions, loudness: value as number})}
                  min={0.3}
                  max={3.0}
                  step={0.1}
                  marks
                />
              </Box>

              <Button
                variant="contained"
                onClick={handleSynthesize}
                disabled={isSynthesizing || !translationData}
                fullWidth
                size="large"
                startIcon={<VolumeUp />}
              >
                {isSynthesizing ? 'Synthesizing...' : 'Generate Speech'}
              </Button>
            </CardContent>
          </Card>

          {synthesisComplete && (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Generated Audio
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<PlayArrow />}
                    fullWidth
                  >
                    Play Audio
                  </Button>
                  
                  <Button
                    variant="contained"
                    startIcon={<Download />}
                    fullWidth
                  >
                    Download Audio
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Synthesis Progress
              </Typography>

              {isSynthesizing && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Generating speech with {TTS_PROVIDERS.find(p => p.id === selectedProvider)?.name}...
                  </Typography>
                  <LinearProgress />
                </Box>
              )}

              {translationData && (
                <Box>
                  <Typography variant="h6" sx={{ mb: 2 }}>
                    Text to Synthesize
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {translationData.translatedSegments.slice(0, 3).map((segment) => (
                      <Paper key={segment.id} sx={{ p: 2, backgroundColor: '#f8fafc' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Chip label={segment.speaker} size="small" />
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
                    Your audio has been generated successfully. You can now play or download the synthesized speech.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default SynthesisPage;
