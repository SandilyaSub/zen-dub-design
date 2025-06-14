
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import { Translate } from '@mui/icons-material';

const Header = () => {
  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{ 
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
        py: 1
      }}
    >
      <Toolbar sx={{ justifyContent: 'center' }}>
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
        <Typography 
          variant="body2" 
          sx={{ 
            position: 'absolute',
            bottom: 8,
            color: 'rgba(255, 255, 255, 0.8)',
            fontSize: '0.875rem'
          }}
        >
          Speech-to-Speech Translation for Indian Languages
        </Typography>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
