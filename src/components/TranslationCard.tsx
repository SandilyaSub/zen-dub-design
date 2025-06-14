
import { useState } from 'react';
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
  TextField
} from '@mui/material';
import { 
  Translate, 
  SwapHoriz,
  CheckCircle 
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
  const [speakerCount, setSpeakerCount] = useState(1);
  const [speakerGender, setSpeakerGender] = useState('Male');
  const [speakerName, setSpeakerName] = useState('');

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
    setTimeout(() => {
      setIsProcessing(false);
      onTranslate();
    }, 2000);
  };

  const swapLanguages = () => {
    onLanguageChange(targetLanguage, sourceLanguage);
  };

  const stepNumber = 2;
  const isStepActive = isActive;
  const isStepCompleted = false;

  return (
    <Card 
      sx={{ 
        border: isStepActive ? '2px solid #6366f1' : '1px solid #e2e8f0',
        opacity: isDisabled ? 0.4 : isStepActive ? 1 : 0.6,
        transition: 'all 0.3s ease'
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Box 
            sx={{ 
              width: 32, 
              height: 32, 
              borderRadius: '50%',
              backgroundColor: isStepCompleted ? '#10b981' : isStepActive ? '#6366f1' : '#94a3b8',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.875rem',
              fontWeight: 600
            }}
          >
            {isStepCompleted ? <CheckCircle sx={{ fontSize: 18 }} /> : stepNumber}
          </Box>
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e293b' }}>
            Step 2: Translation Settings
          </Typography>
        </Box>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 500 }}>
            Target Language
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Translate to:
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FormControl size="small" sx={{ minWidth: 120 }} disabled={isDisabled}>
              <InputLabel>From</InputLabel>
              <Select
                value={sourceLanguage}
                label="From"
                onChange={(e) => onLanguageChange(e.target.value, targetLanguage)}
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
              size="small"
              sx={{ minWidth: 'auto', p: 1 }}
            >
              <SwapHoriz />
            </Button>

            <FormControl size="small" sx={{ minWidth: 120 }} disabled={isDisabled}>
              <InputLabel>To</InputLabel>
              <Select
                value={targetLanguage}
                label="To"
                onChange={(e) => onLanguageChange(sourceLanguage, e.target.value)}
              >
                {languages.map((lang) => (
                  <MenuItem key={lang.code} value={lang.code}>
                    {lang.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 500 }}>
            Character Information
          </Typography>
          
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Number of Speakers:
            </Typography>
            <FormControl size="small" fullWidth disabled={isDisabled}>
              <Select
                value={speakerCount}
                onChange={(e) => setSpeakerCount(Number(e.target.value))}
              >
                <MenuItem value={1}>1</MenuItem>
                <MenuItem value={2}>2</MenuItem>
                <MenuItem value={3}>3</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Speaker 1 Gender:
            </Typography>
            <FormControl size="small" fullWidth disabled={isDisabled}>
              <Select
                value={speakerGender}
                onChange={(e) => setSpeakerGender(e.target.value)}
              >
                <MenuItem value="Male">Male</MenuItem>
                <MenuItem value="Female">Female</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Name (Optional):
            </Typography>
            <TextField
              size="small"
              fullWidth
              placeholder="Enter name"
              value={speakerName}
              onChange={(e) => setSpeakerName(e.target.value)}
              disabled={isDisabled}
            />
          </Box>
        </Box>

        <Button
          variant="contained"
          startIcon={<Translate />}
          onClick={handleTranslate}
          disabled={isProcessing || isDisabled}
          fullWidth
          sx={{ 
            py: 1.5,
            fontWeight: 500
          }}
        >
          {isProcessing ? 'Processing...' : 'Continue'}
        </Button>
      </CardContent>
    </Card>
  );
};

export default TranslationCard;
