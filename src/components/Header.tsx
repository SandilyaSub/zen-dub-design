
import React from 'react';
import { AppBar, Toolbar, Typography, Box } from '@mui/material';
import { RecordVoiceOver } from '@mui/icons-material';

const Header = () => {
  return (
    <AppBar 
      position="static" 
      elevation={0}
      sx={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        borderRadius: '0 0 24px 24px'
      }}
    >
      <Toolbar sx={{ justifyContent: 'center', py: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <RecordVoiceOver sx={{ fontSize: 32, color: 'white' }} />
          <Typography 
            variant="h4" 
            component="h1" 
            sx={{ 
              fontWeight: 300,
              color: 'white',
              letterSpacing: '0.5px'
            }}
          >
            Zen Dubbb
          </Typography>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
