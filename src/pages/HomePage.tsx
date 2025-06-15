
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
  InputLabel
} from '@mui/material';
import { 
  ArrowForward 
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';
import AudioUploadCard from '../components/AudioUploadCard';
import AdvancedFeatures from '../components/AdvancedFeatures';

const HomePage = () => {
  const navigate = useNavigate();
  const { setCurrentStep, setInputData } = useSession();
  const [selectedLanguage, setSelectedLanguage] = useState('Hindi');
  const [audioFile] = useState<File | null>(null);
  const [videoUrl] = useState('');
  const [uploadCompleted, setUploadCompleted] = useState(false);

  const handleUpload = (fileName: string) => {
    console.log('Upload completed:', fileName);
    setUploadCompleted(true);
  };

  const handleContinue = () => {
    // Store input data in session
    setInputData({
      audioFile,
      videoUrl,
      targetLanguage: selectedLanguage,
      uploadedAt: new Date().toISOString()
    });
    
    setCurrentStep('transcription');
    navigate('/transcription');
  };

  return (
    <Box sx={{ minHeight: 'calc(100vh - 120px)', backgroundColor: '#f8fafc' }}>
      <Container maxWidth="lg" sx={{ py: 0 }}>
        <ProgressSteps />
        
        <Box sx={{ textAlign: 'center', mb: 4, px: 2 }}>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2, color: '#1f2937' }}>
            Audio Input & Setup
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ fontSize: '1.125rem' }}>
            Upload audio or extract from video
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 4, mb: 4 }}>
          {/* Audio Upload Section */}
          <Box sx={{ flex: 2 }}>
            <AudioUploadCard 
              onUpload={handleUpload}
              isActive={true}
              isCompleted={uploadCompleted}
            />
          </Box>

          {/* Configuration Section */}
          <Box sx={{ flex: 1 }}>
            <Card sx={{ mb: 3, height: 'fit-content' }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                  Target Language
                </Typography>
                
                <FormControl fullWidth>
                  <InputLabel id="language-select-label">Select Target Language</InputLabel>
                  <Select
                    labelId="language-select-label"
                    value={selectedLanguage}
                    label="Select Target Language"
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                  >
                    <MenuItem value="Hindi">Hindi</MenuItem>
                    <MenuItem value="Telugu">Telugu</MenuItem>
                    <MenuItem value="Tamil">Tamil</MenuItem>
                    <MenuItem value="Kannada">Kannada</MenuItem>
                    <MenuItem value="Bengali">Bengali</MenuItem>
                    <MenuItem value="Malayalam">Malayalam</MenuItem>
                    <MenuItem value="Gujarati">Gujarati</MenuItem>
                    <MenuItem value="Marathi">Marathi</MenuItem>
                    <MenuItem value="Punjabi">Punjabi</MenuItem>
                    <MenuItem value="Odia">Odia</MenuItem>
                  </Select>
                </FormControl>

                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Please specify the language in which you desire the output audio.
                </Typography>

                <Button
                  variant="contained"
                  onClick={handleContinue}
                  disabled={!audioFile && !videoUrl}
                  fullWidth
                  size="large"
                  endIcon={<ArrowForward />}
                  sx={{ mt: 3, py: 1.5 }}
                >
                  Continue to Transcription
                </Button>
              </CardContent>
            </Card>
            
            <AdvancedFeatures />
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default HomePage;
