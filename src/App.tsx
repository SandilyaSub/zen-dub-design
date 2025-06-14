
import React, { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box, Grid } from '@mui/material';
import Header from './components/Header';
import AudioUploadCard from './components/AudioUploadCard';
import TranslationCard from './components/TranslationCard';
import ResultsCard from './components/ResultsCard';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f7fa',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 300,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
        },
      },
    },
  },
});

export type AppStep = 'upload' | 'translate' | 'results';

function App() {
  const [currentStep, setCurrentStep] = useState<AppStep>('upload');
  const [audioFile, setAudioFile] = useState<string | null>(null);
  const [sourceLanguage, setSourceLanguage] = useState('english');
  const [targetLanguage, setTargetLanguage] = useState('hindi');
  const [translationComplete, setTranslationComplete] = useState(false);

  const handleAudioUpload = (fileName: string) => {
    setAudioFile(fileName);
    setCurrentStep('translate');
  };

  const handleTranslationStart = () => {
    setCurrentStep('results');
    setTranslationComplete(true);
  };

  const handleLanguageChange = (source: string, target: string) => {
    setSourceLanguage(source);
    setTargetLanguage(target);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', backgroundColor: '#f5f7fa' }}>
        <Header />
        
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Grid container spacing={4}>
            <Grid item xs={12} md={6}>
              <AudioUploadCard 
                onUpload={handleAudioUpload}
                isActive={currentStep === 'upload'}
                isCompleted={audioFile !== null}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TranslationCard 
                onTranslate={handleTranslationStart}
                onLanguageChange={handleLanguageChange}
                isActive={currentStep === 'translate'}
                isDisabled={!audioFile}
                sourceLanguage={sourceLanguage}
                targetLanguage={targetLanguage}
              />
            </Grid>
            <Grid item xs={12}>
              <ResultsCard 
                isActive={currentStep === 'results'}
                sourceLanguage={sourceLanguage}
                targetLanguage={targetLanguage}
                audioFile={audioFile}
                isVisible={translationComplete}
              />
            </Grid>
          </Grid>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
