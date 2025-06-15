import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  FormControl,
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
  Person,
  ArrowForward
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
  const { translationData, setSynthesisData, setCurrentStep } = useSession();
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
      // Create a simple mock audio URL - a short base64 encoded audio file
      const mockAudioUrl = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmEcBjqX4PO8bCABKEVzxu7Xmi0GM3fH8N2NQRQLV6zn67hVGAhQp+jx0GMbBDAa6e/QgC8EDXnB8NqQQAoUXrTp66hVFApGn+DyvmEcBjqX4PO8bCABKEVzxu7Xmi0GM3fH8N2NQRQLV6zn67hVGAhQp+jx0GMbBzAa6e/QgC8EDXnB8NqQQAoUXrTp66hVFApGn+DyvmEcBjqX4PO8bCABKEVzxu7Xmi0GM3fH8N2NQRQLV6zn67hVGAhQp+jx0GMbBzAa6e/QgC8EDXnB8NqQ==';
      
      setAudioUrl(mockAudioUrl);
      setSynthesisComplete(true);
      setIsSynthesizing(false);
      
      // Store synthesis data in session
      setSynthesisData({
        audioUrl: mockAudioUrl,
        speakerMappings,
        synthesizedAt: new Date().toISOString()
      });
    }, 3000);
  };

  const handleDownload = () => {
    if (audioUrl) {
      const link = document.createElement('a');
      link.href = audioUrl;
      link.download = 'synthesized_speech.wav';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const handleContinueToValidation = () => {
    setCurrentStep('validation');
    navigate('/validation');
  };

  if (!translationData) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No translation data available. Please complete the translation step first.
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <ProgressSteps />
      
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Speech Synthesis
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure voice settings for each speaker and generate synthesized speech
        </Typography>
      </Box>

      {/* Speaker Mapping Configuration */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Person />
            Speaker Voice Mapping ({uniqueSpeakers.length} speakers detected)
          </Typography>
          
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Original Speaker</TableCell>
                  <TableCell>Speaker Name</TableCell>
                  <TableCell>Gender</TableCell>
                  <TableCell>Voice</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {uniqueSpeakers.map((speaker) => (
                  <TableRow key={speaker}>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        {speaker}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        value={speakerMappings[speaker]?.name || speaker}
                        onChange={(e) => handleSpeakerMappingChange(speaker, 'name', e.target.value)}
                        variant="outlined"
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
                            .filter(voice => voice.gender === speakerMappings[speaker]?.gender)
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
        </CardContent>
      </Card>

      {/* Generate Speech Section */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Generate Synthesized Speech
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Click below to generate speech with the configured voice mappings
            </Typography>
            
            {isSynthesizing && (
              <Box sx={{ mb: 3 }}>
                <LinearProgress />
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Synthesizing speech...
                </Typography>
              </Box>
            )}
            
            <Button
              variant="contained"
              size="large"
              onClick={handleSynthesize}
              disabled={isSynthesizing}
              startIcon={<VolumeUp />}
              sx={{ minWidth: 200 }}
            >
              {isSynthesizing ? 'Generating...' : 'Generate Speech'}
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Audio Player Section */}
      {synthesisComplete && audioUrl && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PlayArrow />
              Synthesized Audio
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <audio controls style={{ width: '100%' }}>
                <source src={audioUrl} type="audio/wav" />
                Your browser does not support the audio element.
              </audio>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="outlined"
                onClick={handleDownload}
                startIcon={<Download />}
              >
                Download Audio
              </Button>
              <Button
                variant="contained"
                onClick={handleContinueToValidation}
                startIcon={<ArrowForward />}
                size="large"
              >
                Continue to Validation
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}
    </Container>
  );
};

export default SynthesisPage;
