import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Grid2 as Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Chip
} from '@mui/material';
import { 
  AutoFixHigh
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';

const INDIC_SCRIPTS = [
  { code: 'hi', name: 'Hindi (Devanagari)', script: 'देवनागरी' },
  { code: 'te', name: 'Telugu', script: 'తెలుగు' },
  { code: 'ta', name: 'Tamil', script: 'தமிழ்' },
  { code: 'kn', name: 'Kannada', script: 'ಕನ್ನಡ' },
  { code: 'gu', name: 'Gujarati', script: 'ગુજરાતી' },
  { code: 'mr', name: 'Marathi', script: 'मराठी' },
  { code: 'bn', name: 'Bengali', script: 'বাংলা' },
  { code: 'pa', name: 'Punjabi', script: 'ਪੰਜਾਬੀ' },
  { code: 'ml', name: 'Malayalam', script: 'മലയാളം' },
  { code: 'or', name: 'Odia', script: 'ଓଡ଼ିଆ' }
];

const TransliterationPage = () => {
  const navigate = useNavigate();
  const { transcriptionData, setCurrentStep } = useSession();
  const [romanText, setRomanText] = useState('');
  const [targetScript, setTargetScript] = useState('hi');
  const [transliteratedText, setTransliteratedText] = useState('');
  const [isTransliterating, setIsTransliterating] = useState(false);

  const handleTransliterate = () => {
    if (!romanText.trim()) return;
    
    setIsTransliterating(true);
    
    // Mock transliteration based on target script
    setTimeout(() => {
      const mockTransliterations: { [key: string]: string } = {
        'hi': 'नमस्ते, आज हम बात करेंगे भारतीय भाषाओं के बारे में।',
        'te': 'నమస్తే, ఈరోజు మనం భారతీయ భాషల గురించి మాట్లాడుతాము.',
        'ta': 'வணக்கம், இன்று நாம் இந்திய மொழிகளைப் பற்றி பேசுவோம்.',
        'kn': 'ನಮಸ್ತೆ, ಇಂದು ನಾವು ಭಾರತೀಯ ಭಾಷೆಗಳ ಬಗ್ಗೆ ಮಾತನಾಡುತ್ತೇವೆ.',
        'gu': 'નમસ્તે, આજે આપણે ભારતીય ભાષાઓ વિશે વાત કરીશું.',
        'mr': 'नमस्ते, आज आपण भारतीय भाषांबद्दल बोलणार आहोत.',
        'bn': 'নমস্তে, আজ আমরা ভারতীয় ভাষা নিয়ে কথা বলব।',
        'pa': 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ, ਅੱਜ ਅਸੀਂ ਭਾਰਤੀ ਭਾਸ਼ਾਵਾਂ ਬਾਰੇ ਗੱਲ ਕਰਾਂਗੇ।',
        'ml': 'നമസ്തേ, ഇന്ന് നാം ഇന്ത്യൻ ഭാഷകളെക്കുറിച്ച് സംസാരിക്കും.',
        'or': 'ନମସ୍କାର, ଆଜି ଆମେ ଭାରତୀୟ ଭାଷା ବିଷୟରେ କଥା ହେବା।'
      };
      
      setTransliteratedText(mockTransliterations[targetScript] || romanText);
      setIsTransliterating(false);
    }, 1500);
  };

  const handleContinue = () => {
    setCurrentStep('translation');
    navigate('/translation');
  };

  const handleSkip = () => {
    setCurrentStep('translation');
    navigate('/translation');
  };

  const selectedScript = INDIC_SCRIPTS.find(s => s.code === targetScript);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
          Transliteration
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Convert Roman script to Indic scripts using Google Input Tools
        </Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid xs={12} md={8}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 3 }}>
                Roman Script Input
              </Typography>
              
              <TextField
                fullWidth
                multiline
                rows={6}
                placeholder="Type text in Roman script (e.g., 'namaste, aaj hum baat karenge bharatiya bhashaon ke bare mein')"
                value={romanText}
                onChange={(e) => setRomanText(e.target.value)}
                sx={{ mb: 3 }}
              />

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <FormControl sx={{ minWidth: 250 }}>
                  <InputLabel>Target Script</InputLabel>
                  <Select
                    value={targetScript}
                    label="Target Script"
                    onChange={(e) => setTargetScript(e.target.value)}
                  >
                    {INDIC_SCRIPTS.map((script) => (
                      <MenuItem key={script.code} value={script.code}>
                        {script.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Button
                  variant="contained"
                  onClick={handleTransliterate}
                  disabled={!romanText.trim() || isTransliterating}
                  startIcon={<AutoFixHigh />}
                >
                  {isTransliterating ? 'Converting...' : 'Transliterate'}
                </Button>
              </Box>

              {selectedScript && (
                <Chip 
                  label={`Converting to ${selectedScript.name} (${selectedScript.script})`}
                  variant="outlined"
                  sx={{ mb: 2 }}
                />
              )}
            </CardContent>
          </Card>

          {transliteratedText && (
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Transliterated Text
                </Typography>
                
                <Paper 
                  sx={{ 
                    p: 3, 
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e5e7eb',
                    fontSize: '1.2rem',
                    lineHeight: 1.8,
                    fontFamily: selectedScript?.code === 'ta' ? 'Noto Sans Tamil' : 
                                selectedScript?.code === 'te' ? 'Noto Sans Telugu' :
                                selectedScript?.code === 'kn' ? 'Noto Sans Kannada' :
                                'Noto Sans Devanagari'
                  }}
                >
                  {transliteratedText}
                </Paper>
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                Current Transcription
              </Typography>
              
              {transcriptionData && (
                <Box>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    <strong>Detected Language:</strong> {transcriptionData.detectedLanguage}
                  </Typography>
                  <Typography variant="body2" sx={{ mb: 2 }}>
                    <strong>Segments:</strong> {transcriptionData.segments.length}
                  </Typography>
                  
                  <Paper sx={{ p: 2, maxHeight: 200, overflow: 'auto' }}>
                    {transcriptionData.segments.slice(0, 2).map((segment, index) => (
                      <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                        <strong>{segment.speaker}:</strong> {segment.text.substring(0, 100)}...
                      </Typography>
                    ))}
                  </Paper>
                </Box>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ mb: 2 }}>
                About Transliteration
              </Typography>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Transliteration converts text from Roman script to native Indic scripts. 
                This is particularly useful for:
              </Typography>
              
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                <Chip label="• Typing in native scripts" size="small" variant="outlined" />
                <Chip label="• Preserving pronunciation" size="small" variant="outlined" />
                <Chip label="• Cultural authenticity" size="small" variant="outlined" />
                <Chip label="• Better readability" size="small" variant="outlined" />
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button
                  variant="contained" 
                  onClick={handleContinue}
                  size="large"
                  fullWidth
                >
                  Continue to Translation
                </Button>
                <Button
                  variant="outlined" 
                  onClick={handleSkip}
                  size="large"
                  fullWidth
                >
                  Skip Transliteration
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TransliterationPage;
