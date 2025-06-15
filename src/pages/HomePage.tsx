
import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  TextField,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Alert,
  LinearProgress
} from '@mui/material';
import { 
  CloudUpload, 
  Link as LinkIcon,
  PlayArrow,
  ArrowForward
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const HomePage = () => {
  const navigate = useNavigate();
  const { setInputData, setCurrentStep } = useSession();
  const [inputMethod, setInputMethod] = useState('file');
  const [file, setFile] = useState<File | null>(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Language options
  const languages = [
    { code: 'hindi', name: 'Hindi' },
    { code: 'english', name: 'English' },
    { code: 'telugu', name: 'Telugu' },
    { code: 'tamil', name: 'Tamil' },
    { code: 'kannada', name: 'Kannada' },
    { code: 'gujarati', name: 'Gujarati' },
    { code: 'marathi', name: 'Marathi' },
    { code: 'bengali', name: 'Bengali' }
  ];

  const [sourceLanguage, setSourceLanguage] = useState('hindi');
  const [targetLanguage, setTargetLanguage] = useState('telugu');

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      
      // Create audio URL for preview
      const url = URL.createObjectURL(uploadedFile);
      setAudioUrl(url);
      setProcessingComplete(true);
    }
  };

  const handleUrlProcess = () => {
    if (!videoUrl.trim()) return;
    
    setIsProcessing(true);
    
    // Simulate video processing
    setTimeout(() => {
      // Create a mock audio URL for demonstration
      const mockAudioUrl = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmEcBjqX4PO8bCABKEVzxu7Xmi0GM3fH8N2NQRQLV6zn67hVGAhQp+jx0GMbBzAa6e/QgC8EDXnB8NqQQAoUXrTp66hVFApGn+DyvmEcBjqX4PO8bCABKEVzxu7Xmi0GM3fH8N2NQRQLV6zn67hVGAhQp+jx0GMbBzAa6e/QgC8EDXnB8NqQ==';
      setAudioUrl(mockAudioUrl);
      setIsProcessing(false);
      setProcessingComplete(true);
    }, 2000);
  };

  const handleContinue = () => {
    const inputData = {
      inputMethod,
      file: file || null,
      videoUrl: inputMethod === 'url' ? videoUrl : '',
      sourceLanguage,
      targetLanguage,
      audioUrl
    };
    
    setInputData(inputData);
    setCurrentStep('transcription');
    navigate('/transcription');
  };

  return (
    <Container maxWidth="md" sx={{ py: 3, minHeight: 'calc(100vh - 80px)' }}>
      <ProgressSteps />
      
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h4" component="h1" sx={{ fontWeight: 600, mb: 1 }}>
          Audio Input & Setup
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload an audio file or provide a video URL to get started
        </Typography>
      </Box>

      {/* Language Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Language Configuration
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Source Language</InputLabel>
              <Select
                value={sourceLanguage}
                label="Source Language"
                onChange={(e) => setSourceLanguage(e.target.value)}
              >
                {languages.map((lang) => (
                  <MenuItem key={lang.code} value={lang.code}>
                    {lang.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Target Language</InputLabel>
              <Select
                value={targetLanguage}
                label="Target Language"
                onChange={(e) => setTargetLanguage(e.target.value)}
              >
                {languages.map((lang) => (
                  <MenuItem key={lang.code} value={lang.code}>
                    {lang.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Input Method Selection */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Choose Input Method
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
            <Button
              variant={inputMethod === 'file' ? 'contained' : 'outlined'}
              onClick={() => setInputMethod('file')}
              sx={{ flex: 1 }}
            >
              Upload Audio File
            </Button>
            <Button
              variant={inputMethod === 'url' ? 'contained' : 'outlined'}
              onClick={() => setInputMethod('url')}
              sx={{ flex: 1 }}
            >
              Video URL
            </Button>
          </Box>

          {inputMethod === 'file' && (
            <Box sx={{ textAlign: 'center' }}>
              <input
                accept="audio/*"
                style={{ display: 'none' }}
                id="audio-file-upload"
                type="file"
                onChange={handleFileUpload}
              />
              <label htmlFor="audio-file-upload">
                <Button
                  component="span"
                  variant="outlined"
                  startIcon={<CloudUpload />}
                  size="large"
                  sx={{ mb: 2 }}
                >
                  Choose Audio File
                </Button>
              </label>
              {file && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  File uploaded: {file.name}
                </Alert>
              )}
            </Box>
          )}

          {inputMethod === 'url' && (
            <Box>
              <TextField
                fullWidth
                label="Video URL"
                placeholder="Paste YouTube, Vimeo, or direct video URL here"
                value={videoUrl}
                onChange={(e) => setVideoUrl(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                onClick={handleUrlProcess}
                disabled={!videoUrl.trim() || isProcessing}
                startIcon={<LinkIcon />}
                fullWidth
              >
                {isProcessing ? 'Processing...' : 'Process Video URL'}
              </Button>
              
              {isProcessing && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Extracting audio from video...
                  </Typography>
                  <LinearProgress />
                </Box>
              )}
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Audio Preview (shown after upload/processing) */}
      {processingComplete && audioUrl && (
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <PlayArrow />
              Audio Preview
            </Typography>
            <Box sx={{ mb: 3 }}>
              <audio controls style={{ width: '100%' }}>
                <source src={audioUrl} type="audio/wav" />
                Your browser does not support the audio element.
              </audio>
            </Box>
            <Alert severity="success">
              Upload complete! Audio is ready for transcription.
            </Alert>
          </CardContent>
        </Card>
      )}

      {/* Continue Button */}
      {processingComplete && (
        <Box sx={{ textAlign: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={handleContinue}
            startIcon={<ArrowForward />}
            sx={{ minWidth: 200 }}
          >
            Continue to Transcription
          </Button>
        </Box>
      )}
    </Container>
  );
};

export default HomePage;
