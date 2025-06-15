import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Chip,
  TextField,
  LinearProgress
} from '@mui/material';
import { 
  Translate,
  CompareArrows
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const TRANSLATION_PROVIDERS = [
  { id: 'google', name: 'Google Translate', description: 'Fast and reliable' },
  { id: 'openai', name: 'OpenAI GPT', description: 'Context-aware translations' },
  { id: 'llama', name: 'Meta LLaMA', description: 'Advanced language model' },
  { id: 'claude', name: 'Anthropic Claude', description: 'Nuanced translations' },
  { id: 'sarvam', name: 'Sarvam AI', description: 'Optimized for Indian languages' }
];

const LANGUAGES = [
  'Hindi', 'English', 'Telugu', 'Tamil', 'Kannada', 'Gujarati', 
  'Marathi', 'Bengali', 'Punjabi', 'Malayalam', 'Odia'
];

const TranslationPage = () => {
  const navigate = useNavigate();
  const { transcriptionData, setTranslationData, setCurrentStep } = useSession();
  const [selectedProvider, setSelectedProvider] = useState('sarvam');
  const [sourceLanguage, setSourceLanguage] = useState('Hindi');
  const [targetLanguage, setTargetLanguage] = useState('English');
  const [isTranslating, setIsTranslating] = useState(false);
  const [translatedSegments, setTranslatedSegments] = useState<Array<{
    id: string;
    originalText: string;
    translatedText: string;
    speaker: string;
  }>>([]);

  const handleTranslate = () => {
    if (!transcriptionData) return;
    
    setIsTranslating(true);
    
    setTimeout(() => {
      // Mock translation results
      const mockTranslations = transcriptionData.segments.map(segment => ({
        id: segment.id,
        originalText: segment.text,
        translatedText: targetLanguage === 'English' 
          ? `Hello, today we will talk about Indian languages. This is very interesting topic. How many languages are spoken in India? About 1600+ languages are spoken in India, of which 22 are constitutionally recognized.`
          : `नमस्ते, आज हम भारतीय भाषाओं के बारे में बात करेंगे। यह बहुत दिलचस्प विषय है। भारत में कितनी भाषाएं बोली जाती हैं?`,
        speaker: segment.speaker
      }));
      
      setTranslatedSegments(mockTranslations);
      setIsTranslating(false);
    }, 3000);
  };

  const handleContinue = () => {
    if (translatedSegments.length > 0) {
      setTranslationData({
        provider: selectedProvider as any,
        sourceLanguage,
        targetLanguage,
        translatedSegments,
        metrics: {
          bertScore: 0.89,
          bleuScore: 0.76,
          wordPreservation: 0.82,
          compositeScore: 0.83
        }
      });
    }
    setCurrentStep('synthesis');
    navigate('/synthesis');
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <ProgressSteps />
      
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
          Multi-Provider Translation
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Translate using Google, OpenAI, LLaMA, Claude, or Sarvam AI
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 4, flexDirection: { xs: 'column', md: 'row' } }}>
        <Box sx={{ flex: 1 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Translation Settings
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Translation Provider</InputLabel>
                <Select
                  value={selectedProvider}
                  label="Translation Provider"
                  onChange={(e) => setSelectedProvider(e.target.value)}
                >
                  {TRANSLATION_PROVIDERS.map((provider) => (
                    <MenuItem key={provider.id} value={provider.id}>
                      {provider.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Source Language</InputLabel>
                <Select
                  value={sourceLanguage}
                  label="Source Language"
                  onChange={(e) => setSourceLanguage(e.target.value)}
                >
                  {LANGUAGES.map((lang) => (
                    <MenuItem key={lang} value={lang}>
                      {lang}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Target Language</InputLabel>
                <Select
                  value={targetLanguage}
                  label="Target Language"
                  onChange={(e) => setTargetLanguage(e.target.value)}
                >
                  {LANGUAGES.map((lang) => (
                    <MenuItem key={lang} value={lang}>
                      {lang}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Button
                variant="contained"
                onClick={handleTranslate}
                disabled={isTranslating || !transcriptionData}
                fullWidth
                size="large"
                startIcon={<Translate />}
              >
                {isTranslating ? 'Translating...' : 'Start Translation'}
              </Button>

              {translatedSegments.length > 0 && (
                <Button
                  variant="outlined"
                  onClick={handleContinue}
                  fullWidth
                  size="large"
                  sx={{ mt: 2 }}
                >
                  Continue to Synthesis
                </Button>
              )}
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: 2 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Translation Results
              </Typography>

              {isTranslating && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    Translating with {TRANSLATION_PROVIDERS.find(p => p.id === selectedProvider)?.name}...
                  </Typography>
                  <LinearProgress />
                </Box>
              )}

              {translatedSegments.length > 0 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {translatedSegments.map((segment) => (
                    <Paper key={segment.id} sx={{ p: 3, border: '1px solid #e5e7eb' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Chip label={segment.speaker} size="small" sx={{ mr: 2 }} />
                        <CompareArrows sx={{ color: '#6366f1', mr: 1 }} />
                        <Typography variant="body2" color="text.secondary">
                          {sourceLanguage} → {targetLanguage}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          Original:
                        </Typography>
                        <Typography variant="body1">
                          {segment.originalText}
                        </Typography>
                      </Box>
                      
                      <Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                          Translated:
                        </Typography>
                        <TextField
                          fullWidth
                          multiline
                          minRows={2}
                          value={segment.translatedText}
                          variant="outlined"
                        />
                      </Box>
                    </Paper>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Container>
  );
};

export default TranslationPage;
