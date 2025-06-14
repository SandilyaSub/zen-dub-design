
import { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box, Grid2 } from '@mui/material';
import Header from './components/Header';
import AudioUploadCard from './components/AudioUploadCard';
import TranslationCard from './components/TranslationCard';
import ResultsCard from './components/ResultsCard';

const theme = createTheme({
  palette: {
    primary: {
      main: '#6366f1',
    },
    secondary: {
      main: '#10b981',
    },
    background: {
      default: '#f8fafc',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 500,
    },
  },
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 500,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
          borderRadius: 12,
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

  const handleStartOver = () => {
    setCurrentStep('upload');
    setAudioFile(null);
    setTranslationComplete(false);
    setSourceLanguage('english');
    setTargetLanguage('hindi');
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', backgroundColor: '#f8fafc' }}>
        <Header />
        
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <Grid2 container spacing={3}>
            <Grid2 xs={12} md={6}>
              <AudioUploadCard 
                onUpload={handleAudioUpload}
                isActive={currentStep === 'upload'}
                isCompleted={audioFile !== null}
              />
            </Grid2>
            <Grid2 xs={12} md={6}>
              <TranslationCard 
                onTranslate={handleTranslationStart}
                onLanguageChange={handleLanguageChange}
                isActive={currentStep === 'translate'}
                isDisabled={!audioFile}
                sourceLanguage={sourceLanguage}
                targetLanguage={targetLanguage}
              />
            </Grid2>
            <Grid2 xs={12}>
              <ResultsCard 
                isActive={currentStep === 'results'}
                sourceLanguage={sourceLanguage}
                targetLanguage={targetLanguage}
                isVisible={translationComplete}
                onStartOver={handleStartOver}
              />
            </Grid2>
          </Grid2>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
