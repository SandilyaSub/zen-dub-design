
import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material';
import { Translate } from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSession } from '../context/SessionContext';

const Header = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { currentStep, resetSession } = useSession();

  const navigationItems = [
    { path: '/', label: 'Input', step: 'input' },
    { path: '/transcription', label: 'Transcription', step: 'transcription' },
    { path: '/transliteration', label: 'Transliteration', step: 'transliteration' },
    { path: '/translation', label: 'Translation', step: 'translation' },
    { path: '/synthesis', label: 'Synthesis', step: 'synthesis' },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const handleReset = () => {
    resetSession();
    navigate('/');
  };

  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{ 
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        py: 1
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Translate sx={{ fontSize: 28, color: 'white' }} />
          <Typography 
            variant="h5" 
            component="h1" 
            sx={{ 
              fontWeight: 600,
              color: 'white',
              letterSpacing: '-0.025em'
            }}
          >
            Indic-Translator
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {navigationItems.map((item) => (
            <Button
              key={item.path}
              onClick={() => handleNavigation(item.path)}
              sx={{
                color: location.pathname === item.path ? '#fbbf24' : 'rgba(255, 255, 255, 0.7)',
                fontWeight: location.pathname === item.path ? 600 : 400,
                '&:hover': {
                  color: 'white',
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        <Button
          onClick={handleReset}
          sx={{
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          New Session
        </Button>
      </Toolbar>
      
      <Box sx={{ px: 2, pb: 1 }}>
        <Typography 
          variant="body2" 
          sx={{ 
            color: 'rgba(255, 255, 255, 0.8)',
            fontSize: '0.875rem',
            textAlign: 'center'
          }}
        >
          Speech-to-Speech Translation for Indian Languages
        </Typography>
      </Box>
    </AppBar>
  );
};

export default Header;
