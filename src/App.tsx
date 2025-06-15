
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import Header from './components/Header';
import HomePage from './pages/HomePage';
import TranscriptionPage from './pages/TranscriptionPage';
import TranslationPage from './pages/TranslationPage';
import SynthesisPage from './pages/SynthesisPage';
import ValidationPage from './pages/ValidationPage';
import SessionProvider from './context/SessionContext';

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

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SessionProvider>
        <Router>
          <Header />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/transcription" element={<TranscriptionPage />} />
            <Route path="/translation" element={<TranslationPage />} />
            <Route path="/synthesis" element={<SynthesisPage />} />
            <Route path="/validation" element={<ValidationPage />} />
          </Routes>
        </Router>
      </SessionProvider>
    </ThemeProvider>
  );
}

export default App;
