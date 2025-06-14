
import { useState } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Container, Box } from '@mui/material';
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

  console.log('App rendering with currentStep:', currentStep);

  const handleAudioUpload = (fileName: string) => {
    console.log('Audio uploaded:', fileName);
    setAudioFile(fileName);
    setCurrentStep('translate');
  };

  const handleTranslationStart = () => {
    console.log('Translation started');
    setCurrentStep('results');
    setTranslationComplete(true);
  };

  const handleLanguageChange = (source: string, target: string) => {
    console.log('Language changed:', source, 'to', target);
    setSourceLanguage(source);
    setTargetLanguage(target);
  };

  const handleStartOver = () => {
    console.log('Starting over');
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
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
            gap: 3,
            mb: 3
          }}>
            <AudioUploadCard 
              onUpload={handleAudioUpload}
              isActive={currentStep === 'upload'}
              isCompleted={audioFile !== null}
            />
            <TranslationCard 
              onTranslate={handleTranslationStart}
              onLanguageChange={handleLanguageChange}
              isActive={currentStep === 'translate'}
              isDisabled={!audioFile}
              sourceLanguage={sourceLanguage}
              targetLanguage={targetLanguage}
            />
          </Box>
          <ResultsCard 
            isActive={currentStep === 'results'}
            sourceLanguage={sourceLanguage}
            targetLanguage={targetLanguage}
            isVisible={translationComplete}
            onStartOver={handleStartOver}
          />
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
