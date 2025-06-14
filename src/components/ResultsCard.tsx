
import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Divider,
  Paper
} from '@mui/material';
import { 
  PlayArrow, 
  Download,
  VolumeUp,
  Subtitles 
} from '@mui/icons-material';

const ResultsCard = () => {
  return (
    <Card 
      elevation={2}
      sx={{ 
        borderRadius: 3,
        background: 'linear-gradient(145deg, #f3e5f5 0%, #ffffff 100%)',
        border: '1px solid #e1bee7'
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500, color: '#7b1fa2' }}>
            Translation Results
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Your translated audio is ready
          </Typography>
        </Box>

        <Paper 
          elevation={1} 
          sx={{ 
            p: 3, 
            mb: 3,
            borderRadius: 2,
            backgroundColor: '#fafafa'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Subtitles color="primary" />
            <Typography variant="subtitle2" color="primary">
              Original Transcript
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            "Hello, welcome to our speech translation demo. This is a sample text that will be translated."
          </Typography>
        </Paper>

        <Paper 
          elevation={1} 
          sx={{ 
            p: 3, 
            mb: 3,
            borderRadius: 2,
            backgroundColor: '#f8f9fa'
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
            <Subtitles color="secondary" />
            <Typography variant="subtitle2" color="secondary">
              Translated Text
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            "नमस्ते, हमारे स्पीच ट्रांसलेशन डेमो में आपका स्वागत है। यह एक नमूना टेक्स्ट है जिसका अनुवाद किया जाएगा।"
          </Typography>
        </Paper>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<PlayArrow />}
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              px: 3
            }}
          >
            Play Original
          </Button>
          <Button
            variant="contained"
            startIcon={<VolumeUp />}
            color="secondary"
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              px: 3
            }}
          >
            Play Translation
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            sx={{ 
              borderRadius: 2,
              textTransform: 'none',
              px: 3
            }}
          >
            Download
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ResultsCard;
