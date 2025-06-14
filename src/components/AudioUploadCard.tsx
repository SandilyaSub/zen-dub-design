
import React, { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Button,
  LinearProgress,
  Chip
} from '@mui/material';
import { 
  CloudUpload, 
  Mic, 
  AudioFile,
  CheckCircle 
} from '@mui/icons-material';

const AudioUploadCard = () => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploaded, setIsUploaded] = useState(false);

  const handleFileUpload = () => {
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploaded(true);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  return (
    <Card 
      elevation={2}
      sx={{ 
        borderRadius: 3,
        background: 'linear-gradient(145deg, #f8f9ff 0%, #ffffff 100%)',
        border: '1px solid #e3f2fd'
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 500, color: '#1976d2' }}>
            Upload Audio File
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Support for MP3, WAV, M4A files up to 50MB
          </Typography>
        </Box>

        {!isUploaded ? (
          <Box sx={{ textAlign: 'center' }}>
            <Box 
              sx={{ 
                border: '2px dashed #e0e0e0',
                borderRadius: 2,
                p: 4,
                mb: 3,
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: '#1976d2',
                  backgroundColor: '#f8f9ff'
                }
              }}
            >
              <CloudUpload sx={{ fontSize: 48, color: '#bdbdbd', mb: 2 }} />
              <Typography variant="body1" color="text.secondary" gutterBottom>
                Drag & drop your audio file here
              </Typography>
              <Typography variant="body2" color="text.secondary">
                or click to browse
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                startIcon={<AudioFile />}
                onClick={handleFileUpload}
                sx={{ 
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3
                }}
              >
                Choose File
              </Button>
              <Button
                variant="outlined"
                startIcon={<Mic />}
                sx={{ 
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3
                }}
              >
                Record Live
              </Button>
            </Box>

            {uploadProgress > 0 && uploadProgress < 100 && (
              <Box sx={{ mt: 3 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={uploadProgress}
                  sx={{ 
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: '#e3f2fd'
                  }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                  Uploading... {uploadProgress}%
                </Typography>
              </Box>
            )}
          </Box>
        ) : (
          <Box sx={{ textAlign: 'center' }}>
            <CheckCircle sx={{ fontSize: 48, color: '#4caf50', mb: 2 }} />
            <Typography variant="h6" color="success.main" gutterBottom>
              Upload Complete!
            </Typography>
            <Chip 
              label="audio_sample.mp3" 
              variant="outlined" 
              sx={{ mt: 1 }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AudioUploadCard;
