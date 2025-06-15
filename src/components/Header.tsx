
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
        py: 1
      }}
    >
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Translate sx={{ fontSize: 28, color: 'white' }} />
          <Box>
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
            <Typography 
              variant="body2" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '0.875rem'
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
            border: '1px solid rgba(255, 255, 255, 0.3)',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
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
