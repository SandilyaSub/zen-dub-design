
import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Tab,
  Tabs,
  TextField,
  LinearProgress,
  Chip,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { 
  CloudUpload, 
  AudioFile,
  Link as LinkIcon,
  Mic,
  CheckCircle,
  PlayArrow
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';

const SUPPORTED_LANGUAGES = [
  'Hindi', 'Telugu', 'Tamil', 'Kannada', 'Gujarati', 'Marathi', 
  'Bengali', 'Punjabi', 'Malayalam', 'Odia', 'Assamese', 'Nepali', 
  'Sanskrit', 'Sinhalese', 'Urdu', 'English'
];

const HomePage = () => {
  const navigate = useNavigate();
  const { setAudioData, setCurrentStep } = useSession();
  const [activeTab, setActiveTab] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [videoUrl, setVideoUrl] = useState('');
  const [targetLanguage, setTargetLanguage] = useState('Hindi');
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);

  const handleFileUpload = () => {
    setIsUploading(true);
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          const fileName = 'sample_audio.mp3';
          setUploadedFile(fileName);
          setAudioData({ fileName, file: null });
          return 100;
        }
        return prev + 20;
      });
    }, 300);
  };

  const handleVideoUrlUpload = () => {
    if (!videoUrl.trim()) return;
    
    setIsUploading(true);
    setTimeout(() => {
      setIsUploading(false);
      const fileName = 'extracted_audio.mp3';
      setUploadedFile(fileName);
      setAudioData({ fileName, url: videoUrl });
      setVideoUrl('');
    }, 2000);
  };

  const handleRecording = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      // Start recording
      setTimeout(() => {
        setIsRecording(false);
        const fileName = 'recorded_audio.wav';
        setUploadedFile(fileName);
        setAudioData({ fileName, file: null });
      }, 3000);
    }
  };

  const handleContinue = () => {
    setCurrentStep('transcription');
    navigate('/transcription');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
          Audio Input & Setup
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Upload audio, extract from video, or record directly
        </Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
                <Tab icon={<AudioFile />} label="Upload Audio" />
                <Tab icon={<LinkIcon />} label="Video URL" />
                <Tab icon={<Mic />} label="Record" />
              </Tabs>

              {activeTab === 0 && (
                <Box>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    Upload MP3, WAV, or other audio formats
                  </Typography>
                  
                  <Box 
                    sx={{ 
                      border: '2px dashed #cbd5e1',
                      borderRadius: 2,
                      p: 4,
                      mb: 3,
                      textAlign: 'center',
                      backgroundColor: '#f8fafc',
                      cursor: 'pointer',
                      '&:hover': {
                        borderColor: '#6366f1',
                        backgroundColor: '#f1f5f9'
                      }
                    }}
                  >
                    <CloudUpload sx={{ fontSize: 48, color: '#94a3b8', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      Choose file or drag and drop
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Supports MP3, WAV, M4A, FLAC
                    </Typography>
                  </Box>

                  <Button
                    variant="contained"
                    onClick={handleFileUpload}
                    disabled={isUploading}
                    fullWidth
                    size="large"
                  >
                    {isUploading ? 'Uploading...' : 'Choose Audio File'}
                  </Button>
                </Box>
              )}

              {activeTab === 1 && (
                <Box>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    Extract audio from YouTube, Instagram, or other video platforms
                  </Typography>
                  
                  <TextField
                    fullWidth
                    label="Video URL"
                    placeholder="Paste YouTube, Instagram, or other video URL"
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
                    sx={{ mb: 3 }}
                  />

                  <Button
                    variant="contained"
                    onClick={handleVideoUrlUpload}
                    disabled={!videoUrl.trim() || isUploading}
                    fullWidth
                    size="large"
                  >
                    {isUploading ? 'Extracting Audio...' : 'Extract Audio'}
                  </Button>
                </Box>
              )}

              {activeTab === 2 && (
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body1" sx={{ mb: 3 }}>
                    Record audio directly from your microphone
                  </Typography>
                  
                  <Button
                    variant={isRecording ? "outlined" : "contained"}
                    onClick={handleRecording}
                    size="large"
                    color={isRecording ? "error" : "primary"}
                    sx={{ 
                      minWidth: 200, 
                      minHeight: 60,
                      fontSize: '1.1rem'
                    }}
                  >
                    {isRecording ? 'Stop Recording' : 'Start Recording'}
                  </Button>

                  {isRecording && (
                    <Box sx={{ mt: 3 }}>
                      <Typography variant="body2" color="error" sx={{ mb: 1 }}>
                        Recording in progress...
                      </Typography>
                      <LinearProgress color="error" />
                    </Box>
                  )}
                </Box>
              )}

              {isUploading && activeTab !== 2 && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={uploadProgress}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              )}

              {uploadedFile && (
                <Box sx={{ mt: 3, textAlign: 'center', p: 3, backgroundColor: '#f0fdf4', borderRadius: 2 }}>
                  <CheckCircle sx={{ fontSize: 48, color: '#10b981', mb: 2 }} />
                  <Typography variant="h6" sx={{ color: '#059669', mb: 1 }}>
                    Upload Complete!
                  </Typography>
                  <Chip 
                    label={uploadedFile} 
                    variant="outlined" 
                    size="medium"
                    icon={<PlayArrow />}
                    sx={{ backgroundColor: '#ecfdf5', borderColor: '#10b981' }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Target Language
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Select Target Language</InputLabel>
                <Select
                  value={targetLanguage}
                  label="Select Target Language"
                  onChange={(e) => setTargetLanguage(e.target.value)}
                >
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <MenuItem key={lang} value={lang}>
                      {lang}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                The system supports automatic language detection, but you can also specify your target language for better accuracy.
              </Typography>

              <Button
                variant="contained" 
                onClick={handleContinue}
                disabled={!uploadedFile}
                fullWidth
                size="large"
              >
                Continue to Transcription
              </Button>
            </CardContent>
          </Card>

          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Supported Features
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip label="Speaker Diarization" size="small" />
                <Chip label="VAD Segmentation" size="small" />
                <Chip label="Multi-format Support" size="small" />
                <Chip label="Video Audio Extraction" size="small" />
                <Chip label="Real-time Recording" size="small" />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default HomePage;
