
import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material';
import { Translate } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';

const Header = () => {
  const navigate = useNavigate();
  const { resetSession } = useSession();

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
        height: 120, // Fixed height - using transcription page as baseline
        minHeight: 120
      }}
    >
      <Toolbar sx={{ 
        justifyContent: 'space-between',
        height: '100%',
        minHeight: 120, // Match AppBar height
        px: 3,
        alignItems: 'center' // Ensure content is centered vertically
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Translate sx={{ fontSize: 32, color: 'white' }} />
          <Box>
            <Typography 
              variant="h4" 
              component="h1" 
              sx={{ 
                fontWeight: 700,
                color: 'white',
                letterSpacing: '-0.025em',
                fontSize: '2rem'
              }}
            >
              Indic-Translator
            </Typography>
            <Typography 
              variant="body1" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.9)',
                fontSize: '1rem',
                fontWeight: 400
              }}
            >
              Speech-to-Speech Translation for Indian Languages
            </Typography>
          </Box>
        </Box>

        <Button
          onClick={handleReset}
          sx={{
            color: 'white',
            border: '2px solid rgba(255, 255, 255, 0.3)',
            px: 3,
            py: 1,
            fontSize: '0.9rem',
            fontWeight: 500,
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              border: '2px solid rgba(255, 255, 255, 0.5)',
            },
          }}
        >
          New Session
        </Button>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
