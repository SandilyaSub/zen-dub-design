
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

interface AudioUploadCardProps {
  onUpload: (fileName: string) => void;
  isActive: boolean;
  isCompleted: boolean;
}

const AudioUploadCard: React.FC<AudioUploadCardProps> = ({ onUpload, isActive, isCompleted }) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = () => {
    setIsUploading(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          onUpload('audio_sample.mp3');
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const cardOpacity = isActive ? 1 : isCompleted ? 0.8 : 0.6;
  const cardBorder = isActive ? '2px solid #1976d2' : isCompleted ? '2px solid #4caf50' : '1px solid #e3f2fd';

  return (
    <Card 
      elevation={2}
      sx={{ 
        borderRadius: 3,
        background: 'linear-gradient(145deg, #f8f9ff 0%, #ffffff 100%)',
        border: cardBorder,
        opacity: cardOpacity,
        transition: 'all 0.3s ease'
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

        {!isCompleted ? (
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
                disabled={isUploading || !isActive}
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
                disabled={isUploading || !isActive}
                sx={{ 
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3
                }}
              >
                Record Live
              </Button>
            </Box>

            {isUploading && (
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
