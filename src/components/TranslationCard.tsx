
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
  SwapHoriz 
} from '@mui/icons-material';

interface TranslationCardProps {
  onTranslate: () => void;
  onLanguageChange: (source: string, target: string) => void;
  isActive: boolean;
  isDisabled: boolean;
  sourceLanguage: string;
  targetLanguage: string;
}

const TranslationCard: React.FC<TranslationCardProps> = ({ 
  onTranslate, 
  onLanguageChange, 
  isActive, 
  isDisabled, 
  sourceLanguage, 
  targetLanguage 
}) => {
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
      onTranslate();
    }, 3000);
  };

  const swapLanguages = () => {
    onLanguageChange(targetLanguage, sourceLanguage);
  };

  const cardOpacity = isDisabled ? 0.5 : isActive ? 1 : 0.8;
  const cardBorder = isActive ? '2px solid #f57c00' : '1px solid #fff3c4';

  return (
    <Card 
      elevation={2}
      sx={{ 
        borderRadius: 3,
        background: 'linear-gradient(145deg, #fff8e1 0%, #ffffff 100%)',
        border: cardBorder,
        opacity: cardOpacity,
        transition: 'all 0.3s ease'
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
          <FormControl fullWidth disabled={isDisabled}>
            <InputLabel>Source Language</InputLabel>
            <Select
              value={sourceLanguage}
              label="Source Language"
              onChange={(e) => onLanguageChange(e.target.value, targetLanguage)}
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
            disabled={isDisabled}
            sx={{ 
              minWidth: 'auto',
              p: 1.5,
              borderRadius: 2
            }}
          >
            <SwapHoriz />
          </Button>

          <FormControl fullWidth disabled={isDisabled}>
            <InputLabel>Target Language</InputLabel>
            <Select
              value={targetLanguage}
              label="Target Language"
              onChange={(e) => onLanguageChange(sourceLanguage, e.target.value)}
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
            disabled={isProcessing || isDisabled}
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
