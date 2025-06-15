
import { useState, useRef } from 'react';
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
  Link as LinkIcon,
  PlayArrow,
  Pause
} from '@mui/icons-material';
import { useSession } from '../context/SessionContext';
import { apiService } from '../services/apiService';

interface AudioUploadCardProps {
  onUpload: (fileName: string, duration: number) => void;
  isActive: boolean;
  isCompleted: boolean;
}

const AudioUploadCard: React.FC<AudioUploadCardProps> = ({ onUpload, isActive, isCompleted }) => {
  const { sessionId, audioData, setAudioData } = useSession();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'url'>('upload');
  const [videoUrl, setVideoUrl] = useState('');
  const [isPlaying, setIsPlaying] = useState(false);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('audio/')) {
      alert('Please select an audio file');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Create object URL for preview
      const objectUrl = URL.createObjectURL(file);
      
      // Update session with file data
      setAudioData({
        file,
        url: objectUrl,
        fileName: file.name,
        duration: null, // Will be set after upload
      });

      // Simulate progress for UI feedback
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Upload to backend
      const result = await apiService.uploadAudio(file, sessionId);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      if (result.success) {
        setAudioData({
          fileName: result.fileName,
          duration: result.duration,
        });
        onUpload(result.fileName, result.duration);
      } else {
        throw new Error(result.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      alert('Upload failed. Please try again.');
      setAudioData({
        file: null,
        url: null,
        fileName: null,
        duration: null,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleVideoUrlUpload = async () => {
    if (!videoUrl.trim()) {
      alert('Please enter a valid URL');
      return;
    }

    setIsUploading(true);
    setUploadProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);

      const result = await apiService.processVideoUrl(videoUrl, sessionId);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      if (result.success) {
        setAudioData({
          fileName: result.fileName,
          duration: result.duration,
          url: null, // Backend will provide the processed audio URL
        });
        onUpload(result.fileName, result.duration);
      } else {
        throw new Error(result.error || 'Video processing failed');
      }
    } catch (error) {
      console.error('Video processing error:', error);
      alert('Video processing failed. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const togglePlayback = () => {
    if (!audioRef.current || !audioData.url) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const stepNumber = 1;

  return (
    <Card 
      sx={{ 
        border: isActive ? '2px solid #6366f1' : '1px solid #e2e8f0',
        backgroundColor: isCompleted ? '#f0fdf4' : 'white',
        opacity: !isActive && !isCompleted ? 0.6 : 1,
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
              backgroundColor: isCompleted ? '#10b981' : isActive ? '#6366f1' : '#94a3b8',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '0.875rem',
              fontWeight: 600
            }}
          >
            {isCompleted ? <CheckCircle sx={{ fontSize: 18 }} /> : stepNumber}
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
                  onClick={() => fileInputRef.current?.click()}
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

                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept="audio/*"
                  style={{ display: 'none' }}
                />

                <Button
                  variant="contained"
                  onClick={() => fileInputRef.current?.click()}
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
                    value={videoUrl}
                    onChange={(e) => setVideoUrl(e.target.value)}
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
                  onClick={handleVideoUrlUpload}
                  disabled={!isActive || isUploading || !videoUrl.trim()}
                  fullWidth
                  sx={{ mb: 2 }}
                >
                  {isUploading ? 'Processing...' : 'Upload Video'}
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
              label={`${audioData.fileName} ${audioData.duration ? `(${formatDuration(audioData.duration)})` : ''}`}
              variant="outlined" 
              size="small"
              sx={{ backgroundColor: '#ecfdf5', borderColor: '#10b981', mb: 2 }}
            />
            
            {audioData.url && (
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={togglePlayback}
                  startIcon={isPlaying ? <Pause /> : <PlayArrow />}
                >
                  {isPlaying ? 'Pause' : 'Play'}
                </Button>
                <audio
                  ref={audioRef}
                  src={audioData.url}
                  onEnded={() => setIsPlaying(false)}
                  onPause={() => setIsPlaying(false)}
                  onPlay={() => setIsPlaying(true)}
                />
              </Box>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AudioUploadCard;
