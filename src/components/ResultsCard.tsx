
import React from 'react';
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
  Subtitles 
} from '@mui/icons-material';

interface ResultsCardProps {
  isActive: boolean;
  sourceLanguage: string;
  targetLanguage: string;
  audioFile: string | null;
  isVisible: boolean;
}

const ResultsCard: React.FC<ResultsCardProps> = ({ 
  isActive, 
  sourceLanguage, 
  targetLanguage, 
  audioFile, 
  isVisible 
}) => {
  const sampleTranslations = {
    english: "Hello, welcome to our speech translation demo. This is a sample text that will be translated.",
    hindi: "नमस्ते, हमारे स्पीच ट्रांसलेशन डेमो में आपका स्वागत है। यह एक नमूना टेक्स्ट है जिसका अनुवाद किया जाएगा।",
    spanish: "Hola, bienvenido a nuestra demostración de traducción de voz. Este es un texto de muestra que será traducido.",
    french: "Bonjour, bienvenue dans notre démonstration de traduction vocale. Ceci est un texte d'exemple qui sera traduit.",
    german: "Hallo, willkommen zu unserer Sprachübersetzungs-Demo. Dies ist ein Beispieltext, der übersetzt wird.",
    chinese: "你好，欢迎来到我们的语音翻译演示。这是一个将被翻译的示例文本。"
  };

  const originalText = sampleTranslations[sourceLanguage as keyof typeof sampleTranslations] || sampleTranslations.english;
  const translatedText = sampleTranslations[targetLanguage as keyof typeof sampleTranslations] || sampleTranslations.hindi;

  const cardBorder = isActive ? '2px solid #7b1fa2' : '1px solid #e1bee7';

  if (!isVisible) {
    return (
      <Card 
        elevation={2}
        sx={{ 
          borderRadius: 3,
          background: 'linear-gradient(145deg, #f3e5f5 0%, #ffffff 100%)',
          border: '1px solid #e1bee7',
          opacity: 0.5
        }}
      >
        <CardContent sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary">
            Translation Results
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Complete the translation to see results here
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Fade in={isVisible} timeout={500}>
      <Card 
        elevation={2}
        sx={{ 
          borderRadius: 3,
          background: 'linear-gradient(145deg, #f3e5f5 0%, #ffffff 100%)',
          border: cardBorder,
          transition: 'all 0.3s ease'
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 500, color: '#7b1fa2' }}>
              Translation Results
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your translated audio is ready
            </Typography>
          </Box>

          <Paper 
            elevation={1} 
            sx={{ 
              p: 3, 
              mb: 3,
              borderRadius: 2,
              backgroundColor: '#fafafa'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Subtitles color="primary" />
              <Typography variant="subtitle2" color="primary">
                Original Transcript ({sourceLanguage})
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              "{originalText}"
            </Typography>
          </Paper>

          <Paper 
            elevation={1} 
            sx={{ 
              p: 3, 
              mb: 3,
              borderRadius: 2,
              backgroundColor: '#f8f9fa'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Subtitles color="secondary" />
              <Typography variant="subtitle2" color="secondary">
                Translated Text ({targetLanguage})
              </Typography>
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              "{translatedText}"
            </Typography>
          </Paper>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<PlayArrow />}
              sx={{ 
                borderRadius: 2,
                textTransform: 'none',
                px: 3
              }}
            >
              Play Original
            </Button>
            <Button
              variant="contained"
              startIcon={<VolumeUp />}
              color="secondary"
              sx={{ 
                borderRadius: 2,
                textTransform: 'none',
                px: 3
              }}
            >
              Play Translation
            </Button>
            <Button
              variant="outlined"
              startIcon={<Download />}
              sx={{ 
                borderRadius: 2,
                textTransform: 'none',
                px: 3
              }}
            >
              Download
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Fade>
  );
};

export default ResultsCard;
