
import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Divider,
  Chip
} from '@mui/material';
import { 
  Translate, 
  PlayArrow, 
  Download,
  SwapHoriz 
} from '@mui/icons-material';

const TranslationCard = () => {
  const [sourceLanguage, setSourceLanguage] = useState('english');
  const [targetLanguage, setTargetLanguage] = useState('hindi');
  const [isProcessing, setIsProcessing] = useState(false);

  const languages = [
    { code: 'english', name: 'English' },
    { code: 'hindi', name: 'Hindi' },
    { code: 'spanish', name: 'Spanish' },
    { code: 'french', name: 'French' },
    { code: 'german', name: 'German' },
    { code: 'chinese', name: 'Chinese' }
  ];

  const handleTranslate = () => {
    setIsProcessing(true);
    // Simulate processing
    setTimeout(() => {
      setIsProcessing(false);
    }, 3000);
  };

  const swapLanguages = () => {
    const temp = sourceLanguage;
    setSourceLanguage(targetLanguage);
    setTargetLanguage(temp);
  };

  return (
    <Card 
      elevation={2}
      sx={{ 
        borderRadius: 3,
        background: 'linear-gradient(145deg, #fff8e1 0%, #ffffff 100%)',
        border: '1px solid #fff3c4'
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500, color: '#f57c00' }}>
            Translation Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Choose source and target languages
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <FormControl fullWidth>
            <InputLabel>Source Language</InputLabel>
            <Select
              value={sourceLanguage}
              label="Source Language"
              onChange={(e) => setSourceLanguage(e.target.value)}
              sx={{ borderRadius: 2 }}
            >
              {languages.map((lang) => (
                <MenuItem key={lang.code} value={lang.code}>
                  {lang.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Button
            onClick={swapLanguages}
            sx={{ 
              minWidth: 'auto',
              p: 1.5,
              borderRadius: 2
            }}
          >
            <SwapHoriz />
          </Button>

          <FormControl fullWidth>
            <InputLabel>Target Language</InputLabel>
            <Select
              value={targetLanguage}
              label="Target Language"
              onChange={(e) => setTargetLanguage(e.target.value)}
              sx={{ borderRadius: 2 }}
            >
              {languages.map((lang) => (
                <MenuItem key={lang.code} value={lang.code}>
                  {lang.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant="contained"
            startIcon={<Translate />}
            onClick={handleTranslate}
            disabled={isProcessing}
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              px: 4,
              py: 1.5,
              background: 'linear-gradient(45deg, #ff6b6b, #ffd93d)',
              '&:hover': {
                background: 'linear-gradient(45deg, #ff5252, #ffcc02)'
              }
            }}
          >
            {isProcessing ? 'Processing...' : 'Start Translation'}
          </Button>
        </Box>

        {isProcessing && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Chip 
              label="AI is working on your translation..." 
              color="primary" 
              sx={{ animation: 'pulse 2s infinite' }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default TranslationCard;
