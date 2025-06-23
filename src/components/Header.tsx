
import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material';
import { Translate } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import { SidebarTrigger } from './ui/sidebar';

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
        height: 64,
        minHeight: 64,
        zIndex: 10
      }}
    >
      <Toolbar sx={{ 
        justifyContent: 'space-between', 
        height: 64,
        minHeight: '64px !important',
        px: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box sx={{ 
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            '& svg': { 
              color: 'white !important',
              fill: 'white !important'
            },
            '& button': {
              color: 'white !important',
              '&:hover': {
                backgroundColor: 'rgba(255, 255, 255, 0.1)'
              }
            }
          }}>
            <SidebarTrigger />
          </Box>
          <Translate sx={{ fontSize: 24, color: 'white' }} />
          <Box>
            <Typography 
              variant="h6" 
              component="h1" 
              sx={{ 
                fontWeight: 600,
                color: 'white',
                letterSpacing: '-0.025em',
                fontSize: '1.25rem'
              }}
            >
              Indic-Translator
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: 'rgba(255, 255, 255, 0.8)',
                fontSize: '0.75rem',
                lineHeight: 1
              }}
            >
              Speech-to-Speech Translation for Indian Languages
            </Typography>
          </Box>
        </Box>

        <Button
          onClick={handleReset}
          size="small"
          sx={{
            color: 'white',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            fontSize: '0.875rem',
            px: 2,
            py: 0.5,
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
