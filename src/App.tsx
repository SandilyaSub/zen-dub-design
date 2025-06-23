
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box } from '@mui/material';
import { SidebarProvider } from './components/ui/sidebar';
import { AppSidebar } from './components/AppSidebar';
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
          <SidebarProvider>
            <div className="min-h-screen flex w-full bg-gray-50">
              <AppSidebar />
              <div className="flex-1 flex flex-col min-h-screen">
                <Header />
                <Box
                  component="main"
                  sx={{
                    flex: 1,
                    backgroundColor: '#f8fafc',
                    minHeight: 'calc(100vh - 64px)',
                    overflow: 'auto'
                  }}
                >
                  <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/transcription" element={<TranscriptionPage />} />
                    <Route path="/translation" element={<TranslationPage />} />
                    <Route path="/synthesis" element={<SynthesisPage />} />
                    <Route path="/validation" element={<ValidationPage />} />
                  </Routes>
                </Box>
              </div>
            </div>
          </SidebarProvider>
        </Router>
      </SessionProvider>
    </ThemeProvider>
  );
}

export default App;
