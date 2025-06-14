import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Divider,
  Paper,
  Fade
} from '@mui/material';
import { 
  PlayArrow, 
  Download,
  VolumeUp,
  CheckCircle 
} from '@mui/icons-material';

interface ResultsCardProps {
  isActive: boolean;
  sourceLanguage: string;
  targetLanguage: string;
  isVisible: boolean;
  onStartOver: () => void;
}

const ResultsCard: React.FC<ResultsCardProps> = ({ 
  isActive, 
  sourceLanguage, 
  targetLanguage, 
  isVisible,
  onStartOver
}) => {
  const sampleTranslations = {
    english: "Hello, welcome to our speech translation demo. This is a sample text that will be translated.",
    hindi: "नमस्ते, हमारे स्पीच ट्रांसलेशन डेमो में आपका स्वागत है। यह एक नमूना टेक्स्ट है जिसका अनुवाद किया जाएगा।",
    spanish: "Hola, bienvenido a nuestra demostración de traducción de voz.",
    french: "Bonjour, bienvenue dans notre démonstration de traduction vocale.",
    german: "Hallo, willkommen zu unserer Sprachübersetzungs-Demo.",
    chinese: "你好，欢迎来到我们的语音翻译演示。"
  };

  const originalText = sampleTranslations[sourceLanguage as keyof typeof sampleTranslations] || sampleTranslations.english;
  const translatedText = sampleTranslations[targetLanguage as keyof typeof sampleTranslations] || sampleTranslations.hindi;

  const stepNumber = 3;

  if (!isVisible) {
    return (
      <Card 
        sx={{ 
          border: '1px solid #e2e8f0',
          opacity: 0.4
        }}
      >
        <CardContent sx={{ p: 3, textAlign: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3, justifyContent: 'center' }}>
            <Box 
              sx={{ 
                width: 32, 
                height: 32, 
                borderRadius: '50%',
                backgroundColor: '#94a3b8',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.875rem',
                fontWeight: 600
              }}
            >
              {stepNumber}
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#64748b' }}>
              Step 3: Results
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary">
            Complete the translation to see results here
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Fade in={isVisible} timeout={500}>
      <Card 
        sx={{ 
          border: isActive ? '2px solid #10b981' : '1px solid #e2e8f0',
          backgroundColor: '#f0fdf4'
        }}
      >
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
            <Box 
              sx={{ 
                width: 32, 
                height: 32, 
                borderRadius: '50%',
                backgroundColor: '#10b981',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <CheckCircle sx={{ fontSize: 18 }} />
            </Box>
            <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e293b' }}>
              Step 3: Translation Complete
            </Typography>
          </Box>

          <Typography variant="body1" sx={{ mb: 3, color: '#059669', fontWeight: 500 }}>
            Translating from {sourceLanguage} to {targetLanguage}
          </Typography>

          <Paper 
            elevation={0} 
            sx={{ 
              p: 3, 
              mb: 3,
              backgroundColor: 'white',
              border: '1px solid #e5e7eb'
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 2, color: '#374151', fontWeight: 500 }}>
              Original Transcript
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              "{originalText}"
            </Typography>
          </Paper>

          <Paper 
            elevation={0} 
            sx={{ 
              p: 3, 
              mb: 3,
              backgroundColor: 'white',
              border: '1px solid #e5e7eb'
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 2, color: '#374151', fontWeight: 500 }}>
              Translation
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              "{translatedText}"
            </Typography>
          </Paper>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<PlayArrow />}
                size="small"
              >
                Play Original
              </Button>
              <Button
                variant="outlined"
                startIcon={<VolumeUp />}
                size="small"
              >
                Play Translation
              </Button>
              <Button
                variant="outlined"
                startIcon={<Download />}
                size="small"
              >
                Download
              </Button>
            </Box>
            <Button
              variant="contained"
              onClick={onStartOver}
              size="small"
              sx={{ backgroundColor: '#6366f1' }}
            >
              Start Over
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Fade>
  );
};

export default ResultsCard;
