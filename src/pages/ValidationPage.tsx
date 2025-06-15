import { useState, useEffect } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  LinearProgress,
  Paper,
  Chip,
  Divider
} from '@mui/material';
import { 
  CheckCircle,
  Assessment,
  VolumeUp,
  Translate,
  RecordVoiceOver,
  Download,
  Refresh
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const ValidationPage = () => {
  const navigate = useNavigate();
  const { synthesisData, setValidationData, setCurrentStep } = useSession();
  const [isValidating, setIsValidating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [validationComplete, setValidationComplete] = useState(false);

  const [metrics, setMetrics] = useState({
    semanticSimilarity: 0,
    transcriptionAccuracy: 0,
    translationQuality: 0,
    audioQuality: 0,
    overallScore: 0
  });

  useEffect(() => {
    if (!synthesisData) {
      navigate('/synthesis');
      return;
    }
    
    // Start validation automatically
    handleValidation();
  }, []);

  const handleValidation = () => {
    setIsValidating(true);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsValidating(false);
          setValidationComplete(true);
          
          // Mock validation results
          const mockMetrics = {
            semanticSimilarity: 89,
            transcriptionAccuracy: 94,
            translationQuality: 87,
            audioQuality: 92,
            overallScore: 90
          };
          
          setMetrics(mockMetrics);
          setValidationData(mockMetrics);
          
          return 100;
        }
        return prev + 8;
      });
    }, 250);
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#10b981';
    if (score >= 75) return '#f59e0b';
    return '#ef4444';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Excellent';
    if (score >= 75) return 'Good';
    return 'Needs Improvement';
  };

  const handleStartOver = () => {
    setCurrentStep('input');
    navigate('/');
  };

  return (
    <Box sx={{ minHeight: 'calc(100vh - 100px)' }}> {/* Account for fixed header height */}
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <ProgressSteps />
        
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2 }}>
            Quality Validation
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Comprehensive analysis of translation and synthesis quality
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 4, flexDirection: { xs: 'column', md: 'row' } }}>
          <Box sx={{ flex: 1 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Validation Status
                </Typography>
                
                {isValidating ? (
                  <Box>
                    <Typography variant="body2" sx={{ mb: 2 }}>
                      Running quality checks: {progress}%
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={progress}
                      sx={{ height: 8, borderRadius: 4, mb: 2 }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      Analyzing semantic similarity, translation accuracy, and audio quality...
                    </Typography>
                  </Box>
                ) : (
                  <Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                      <CheckCircle sx={{ color: '#10b981', mr: 1 }} />
                      <Typography variant="body1">
                        Validation Complete
                      </Typography>
                    </Box>
                    
                    <Paper sx={{ p: 3, mb: 3, backgroundColor: '#f0fdf4', border: '1px solid #10b981' }}>
                      <Typography variant="h4" sx={{ color: '#059669', textAlign: 'center', mb: 1 }}>
                        {metrics.overallScore}%
                      </Typography>
                      <Typography variant="body1" sx={{ textAlign: 'center', color: '#059669' }}>
                        Overall Quality Score
                      </Typography>
                      <Typography variant="body2" sx={{ textAlign: 'center', color: '#065f46', mt: 1 }}>
                        {getScoreLabel(metrics.overallScore)}
                      </Typography>
                    </Paper>
                  </Box>
                )}

                <Divider sx={{ my: 3 }} />
                
                <Typography variant="h6" sx={{ mb: 2 }}>
                  Actions
                </Typography>
                
                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  fullWidth
                  sx={{ mb: 2 }}
                  disabled={!validationComplete}
                >
                  Download Final Audio
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={handleStartOver}
                  fullWidth
                >
                  Start New Translation
                </Button>
              </CardContent>
            </Card>
          </Box>

          <Box sx={{ flex: 2 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ mb: 3 }}>
                  Quality Metrics
                </Typography>

                {isValidating ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Assessment sx={{ fontSize: 48, color: '#94a3b8', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary">
                      Analyzing translation and synthesis quality...
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 3 }}>
                    <Paper sx={{ p: 3, textAlign: 'center' }}>
                      <Translate sx={{ fontSize: 32, color: getScoreColor(metrics.semanticSimilarity), mb: 1 }} />
                      <Typography variant="h5" sx={{ color: getScoreColor(metrics.semanticSimilarity), mb: 1 }}>
                        {metrics.semanticSimilarity}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Semantic Similarity
                      </Typography>
                      <Chip 
                        label={getScoreLabel(metrics.semanticSimilarity)}
                        size="small"
                        sx={{ 
                          mt: 1,
                          backgroundColor: `${getScoreColor(metrics.semanticSimilarity)}20`,
                          color: getScoreColor(metrics.semanticSimilarity)
                        }}
                      />
                    </Paper>

                    <Paper sx={{ p: 3, textAlign: 'center' }}>
                      <RecordVoiceOver sx={{ fontSize: 32, color: getScoreColor(metrics.transcriptionAccuracy), mb: 1 }} />
                      <Typography variant="h5" sx={{ color: getScoreColor(metrics.transcriptionAccuracy), mb: 1 }}>
                        {metrics.transcriptionAccuracy}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Transcription Accuracy
                      </Typography>
                      <Chip 
                        label={getScoreLabel(metrics.transcriptionAccuracy)}
                        size="small"
                        sx={{ 
                          mt: 1,
                          backgroundColor: `${getScoreColor(metrics.transcriptionAccuracy)}20`,
                          color: getScoreColor(metrics.transcriptionAccuracy)
                        }}
                      />
                    </Paper>

                    <Paper sx={{ p: 3, textAlign: 'center' }}>
                      <Assessment sx={{ fontSize: 32, color: getScoreColor(metrics.translationQuality), mb: 1 }} />
                      <Typography variant="h5" sx={{ color: getScoreColor(metrics.translationQuality), mb: 1 }}>
                        {metrics.translationQuality}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Translation Quality
                      </Typography>
                      <Chip 
                        label={getScoreLabel(metrics.translationQuality)}
                        size="small"
                        sx={{ 
                          mt: 1,
                          backgroundColor: `${getScoreColor(metrics.translationQuality)}20`,
                          color: getScoreColor(metrics.translationQuality)
                        }}
                      />
                    </Paper>

                    <Paper sx={{ p: 3, textAlign: 'center' }}>
                      <VolumeUp sx={{ fontSize: 32, color: getScoreColor(metrics.audioQuality), mb: 1 }} />
                      <Typography variant="h5" sx={{ color: getScoreColor(metrics.audioQuality), mb: 1 }}>
                        {metrics.audioQuality}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Audio Quality
                      </Typography>
                      <Chip 
                        label={getScoreLabel(metrics.audioQuality)}
                        size="small"
                        sx={{ 
                          mt: 1,
                          backgroundColor: `${getScoreColor(metrics.audioQuality)}20`,
                          color: getScoreColor(metrics.audioQuality)
                        }}
                      />
                    </Paper>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default ValidationPage;
