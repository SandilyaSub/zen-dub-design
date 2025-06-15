
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
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import { 
  CloudUpload, 
  AudioFile,
  Link as LinkIcon,
  CheckCircle,
  PlayArrow
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';
import AdvancedFeatures from '../components/AdvancedFeatures';

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
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          const fileName = 'extracted_audio.mp3';
          setUploadedFile(fileName);
          setAudioData({ fileName, url: videoUrl });
          setVideoUrl('');
          return 100;
        }
        return prev + 20;
      });
    }, 300);
  };

  const handleContinue = () => {
    setCurrentStep('transcription');
    navigate('/transcription');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <ProgressSteps />
      
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
          Audio Input & Setup
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Upload audio or extract from video
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 4, flexDirection: { xs: 'column', md: 'row' } }}>
        <Box sx={{ flex: 2 }}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
                <Tab icon={<AudioFile />} label="Upload Audio" />
                <Tab icon={<LinkIcon />} label="Video URL" />
              </Tabs>

              {activeTab === 0 && (
                <Box>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    Upload MP3, WAV, or other audio formats
                  </Typography>
                  
                  {!uploadedFile ? (
                    <>
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
                        startIcon={isUploading ? undefined : <CloudUpload />}
                      >
                        {isUploading ? 'Uploading...' : 'Choose Audio File'}
                      </Button>
                    </>
                  ) : (
                    <Box sx={{ textAlign: 'center', p: 3, backgroundColor: '#f0fdf4', borderRadius: 2 }}>
                      <CheckCircle sx={{ fontSize: 48, color: '#10b981', mb: 2 }} />
                      <Typography variant="h6" sx={{ color: '#059669', mb: 2 }}>
                        Upload Complete!
                      </Typography>
                      <Chip 
                        label={uploadedFile} 
                        variant="outlined" 
                        size="medium"
                        icon={<PlayArrow />}
                        sx={{ backgroundColor: '#ecfdf5', borderColor: '#10b981', mb: 3 }}
                      />
                      <Box sx={{ mt: 2 }}>
                        <audio controls style={{ width: '100%' }}>
                          <source src="#" type="audio/mpeg" />
                          Your browser does not support the audio element.
                        </audio>
                      </Box>
                    </Box>
                  )}
                </Box>
              )}

              {activeTab === 1 && (
                <Box>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    Extract audio from YouTube, Instagram, or other video platforms
                  </Typography>
                  
                  {!uploadedFile ? (
                    <>
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
                    </>
                  ) : (
                    <Box sx={{ textAlign: 'center', p: 3, backgroundColor: '#f0fdf4', borderRadius: 2 }}>
                      <CheckCircle sx={{ fontSize: 48, color: '#10b981', mb: 2 }} />
                      <Typography variant="h6" sx={{ color: '#059669', mb: 2 }}>
                        Audio Extraction Complete!
                      </Typography>
                      <Chip 
                        label={uploadedFile} 
                        variant="outlined" 
                        size="medium"
                        icon={<PlayArrow />}
                        sx={{ backgroundColor: '#ecfdf5', borderColor: '#10b981', mb: 3 }}
                      />
                      <Box sx={{ mt: 2 }}>
                        <audio controls style={{ width: '100%' }}>
                          <source src="#" type="audio/mpeg" />
                          Your browser does not support the audio element.
                        </audio>
                      </Box>
                    </Box>
                  )}
                </Box>
              )}

              {isUploading && !uploadedFile && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress 
                    variant="determinate" 
                    value={uploadProgress}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: 1 }}>
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
                Please specify the language in which you desire the output audio.
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

          <Box sx={{ mt: 2 }}>
            <AdvancedFeatures />
          </Box>
        </Box>
      </Box>
    </Container>
  );
};

export default HomePage;
