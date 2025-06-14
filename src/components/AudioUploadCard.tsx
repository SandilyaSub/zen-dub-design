import { useState } from 'react';
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
  AudioFile,
  CheckCircle,
  Link as LinkIcon
} from '@mui/icons-material';

interface AudioUploadCardProps {
  onUpload: (fileName: string) => void;
  isActive: boolean;
  isCompleted: boolean;
}

const AudioUploadCard: React.FC<AudioUploadCardProps> = ({ onUpload, isActive, isCompleted }) => {
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'url'>('upload');

  const handleFileUpload = () => {
    setIsUploading(true);
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          onUpload('audio_sample.mp3');
          return 100;
        }
        return prev + 20;
      });
    }, 300);
  };

  const stepNumber = 1;
  const isStepActive = isActive;
  const isStepCompleted = isCompleted;

  return (
    <Card 
      sx={{ 
        border: isStepActive ? '2px solid #6366f1' : '1px solid #e2e8f0',
        backgroundColor: isStepCompleted ? '#f0fdf4' : 'white',
        opacity: !isStepActive && !isStepCompleted ? 0.6 : 1,
        transition: 'all 0.3s ease'
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
          <Box 
            sx={{ 
              width: 32, 
              height: 32, 
              borderRadius: '50%',
              backgroundColor: isStepCompleted ? '#10b981' : isStepActive ? '#6366f1' : '#94a3b8',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.875rem',
              fontWeight: 600
            }}
          >
            {isStepCompleted ? <CheckCircle sx={{ fontSize: 18 }} /> : stepNumber}
          </Box>
          <Typography variant="h6" sx={{ fontWeight: 600, color: '#1e293b' }}>
            Step 1: Input
          </Typography>
        </Box>

        {!isCompleted ? (
          <>
            <Box sx={{ display: 'flex', mb: 3 }}>
              <Button
                variant={activeTab === 'upload' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('upload')}
                startIcon={<AudioFile />}
                sx={{ mr: 1, borderRadius: 1 }}
                size="small"
              >
                Upload Audio
              </Button>
              <Button
                variant={activeTab === 'url' ? 'contained' : 'outlined'}
                onClick={() => setActiveTab('url')}
                startIcon={<LinkIcon />}
                sx={{ borderRadius: 1 }}
                size="small"
              >
                Video URL
              </Button>
            </Box>

            {activeTab === 'upload' ? (
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Upload an MP3 or WAV file
                </Typography>
                
                <Box 
                  sx={{ 
                    border: '2px dashed #cbd5e1',
                    borderRadius: 2,
                    p: 3,
                    mb: 3,
                    textAlign: 'center',
                    backgroundColor: '#f8fafc',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    '&:hover': {
                      borderColor: '#6366f1',
                      backgroundColor: '#f1f5f9'
                    }
                  }}
                >
                  <CloudUpload sx={{ fontSize: 40, color: '#94a3b8', mb: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    Choose file or drag and drop
                  </Typography>
                </Box>

                <Button
                  variant="contained"
                  onClick={handleFileUpload}
                  disabled={isUploading || !isActive}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  {isUploading ? 'Uploading...' : 'Choose Audio File'}
                </Button>
              </Box>
            ) : (
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Extract audio from YouTube or Instagram
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                  <input
                    type="text"
                    placeholder="Paste YouTube or Instagram URL"
                    style={{
                      width: '100%',
                      padding: '12px',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      fontSize: '14px'
                    }}
                  />
                </Box>

                <Button
                  variant="contained"
                  disabled={!isActive}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  Upload Video
                </Button>
              </Box>
            )}

            {isUploading && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress 
                  variant="determinate" 
                  value={uploadProgress}
                  sx={{ height: 6, borderRadius: 3 }}
                />
              </Box>
            )}
          </>
        ) : (
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <CheckCircle sx={{ fontSize: 48, color: '#10b981', mb: 2 }} />
            <Typography variant="h6" sx={{ color: '#059669', mb: 1 }}>
              Upload Complete!
            </Typography>
            <Chip 
              label="audio_sample.mp3" 
              variant="outlined" 
              size="small"
              sx={{ backgroundColor: '#ecfdf5', borderColor: '#10b981' }}
            />
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AudioUploadCard;
