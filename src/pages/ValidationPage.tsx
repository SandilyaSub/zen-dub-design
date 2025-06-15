
import { useState } from 'react';
import { 
  Container, 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Rating,
  TextField,
  LinearProgress
} from '@mui/material';
import { 
  CheckCircle, 
  Download,
  Refresh,
  Star
} from '@mui/icons-material';
import { useSession } from '../context/SessionContext';
import ProgressSteps from '../components/ProgressSteps';

const ValidationPage = () => {
  const { translationData, synthesisData } = useSession();
  const [overallRating, setOverallRating] = useState<number | null>(4);
  const [feedback, setFeedback] = useState('');

  // Mock quality metrics
  const qualityMetrics = [
    { metric: 'BERT Score', value: 0.89, description: 'Semantic similarity' },
    { metric: 'BLEU Score', value: 0.76, description: 'Translation accuracy' },
    { metric: 'Word Preservation', value: 0.82, description: 'Key terms maintained' },
    { metric: 'Composite Score', value: 0.83, description: 'Overall quality' }
  ];

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return '#10b981'; // Green
    if (score >= 0.6) return '#f59e0b'; // Yellow
    return '#ef4444'; // Red
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.6) return 'Good';
    return 'Needs Improvement';
  };

  if (!translationData || !synthesisData) {
    return (
      <Container maxWidth="md" sx={{ py: 3 }}>
        <Typography variant="h6" color="text.secondary">
          Please complete the previous steps to access validation.
        </Typography>
      </Container>
    );
  }

  return (
    <Box sx={{ minHeight: 'calc(100vh - 120px)', backgroundColor: '#f8fafc' }}>
      <Container maxWidth="lg" sx={{ py: 0 }}>
        <ProgressSteps />
        
        <Box sx={{ textAlign: 'center', mb: 4, px: 2 }}>
          <Typography variant="h3" component="h1" sx={{ fontWeight: 700, mb: 2, color: '#1f2937' }}>
            Validation & Quality Check
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ fontSize: '1.125rem' }}>
            Review and validate the complete speech-to-speech translation
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 4, mb: 4 }}>
          {/* Quality Metrics */}
          <Box sx={{ flex: 1 }}>
            <Card sx={{ mb: 3 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                  Quality Metrics
                </Typography>
                
                <TableContainer component={Paper} variant="outlined">
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Metric</TableCell>
                        <TableCell align="center">Score</TableCell>
                        <TableCell align="center">Quality</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {qualityMetrics.map((metric) => (
                        <TableRow key={metric.metric}>
                          <TableCell>
                            <Box>
                              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                {metric.metric}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {metric.description}
                              </Typography>
                            </Box>
                          </TableCell>
                          <TableCell align="center">
                            <Typography variant="h6" sx={{ fontWeight: 600 }}>
                              {metric.value.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={getScoreLabel(metric.value)}
                              sx={{
                                backgroundColor: getScoreColor(metric.value),
                                color: 'white',
                                fontWeight: 500
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>

            {/* User Feedback */}
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                  Your Feedback
                </Typography>
                
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                    Overall Rating
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    <Rating
                      value={overallRating}
                      onChange={(_, newValue) => setOverallRating(newValue)}
                      size="large"
                      icon={<Star sx={{ color: '#fbbf24' }} />}
                      emptyIcon={<Star sx={{ color: '#d1d5db' }} />}
                    />
                    <Typography variant="body2" color="text.secondary">
                      {overallRating ? `${overallRating}/5 stars` : 'No rating'}
                    </Typography>
                  </Box>
                </Box>

                <TextField
                  fullWidth
                  multiline
                  minRows={3}
                  placeholder="Share your feedback about the translation quality, voice synthesis, or overall experience..."
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  variant="outlined"
                  sx={{ mb: 3 }}
                />

                <Button variant="outlined" fullWidth>
                  Submit Feedback
                </Button>
              </CardContent>
            </Card>
          </Box>

          {/* Final Results */}
          <Box sx={{ flex: 2 }}>
            <Card sx={{ mb: 3 }}>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                  Final Audio Output
                </Typography>
                
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <CheckCircle sx={{ color: '#10b981', fontSize: 28 }} />
                  <Box>
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      Processing Complete
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Speech-to-speech translation successful
                    </Typography>
                  </Box>
                </Box>

                <Paper sx={{ p: 2, mb: 3, backgroundColor: '#f9fafb' }}>
                  <Typography variant="body2" sx={{ mb: 2, fontWeight: 500 }}>
                    Translation Summary:
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    • Source: {translationData.sourceLanguage}<br/>
                    • Target: {translationData.targetLanguage}<br/>
                    • Segments: {translationData.translatedSegments.length}<br/>
                    • Quality Score: {qualityMetrics[3].value.toFixed(2)}/1.0
                  </Typography>
                </Paper>

                <Box sx={{ mb: 3 }}>
                  <audio controls style={{ width: '100%' }}>
                    {synthesisData.audioUrl && (
                      <source src={synthesisData.audioUrl} type="audio/wav" />
                    )}
                    Your browser does not support the audio element.
                  </audio>
                </Box>
                
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<Download />}
                    sx={{ flex: 1 }}
                  >
                    Download Audio
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<Refresh />}
                    sx={{ flex: 1 }}
                  >
                    Process Again
                  </Button>
                </Box>
              </CardContent>
            </Card>

            {/* Processing History */}
            <Card>
              <CardContent sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                  Processing Steps
                </Typography>
                
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {[
                    { step: 'Audio Input', status: 'Completed', time: '2.3s' },
                    { step: 'Speech Recognition', status: 'Completed', time: '15.7s' },
                    { step: 'Translation', status: 'Completed', time: '3.1s' },
                    { step: 'Speech Synthesis', status: 'Completed', time: '8.9s' },
                    { step: 'Validation', status: 'In Progress', time: '-' }
                  ].map((item, index) => (
                    <Box key={index} sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        {item.status === 'Completed' ? (
                          <CheckCircle sx={{ color: '#10b981', fontSize: 20 }}/>
                        ) : (
                          <Box sx={{ width: 20, height: 20 }}>
                            <LinearProgress 
                              variant="indeterminate" 
                              sx={{ 
                                height: 4, 
                                borderRadius: 2,
                                mt: 1
                              }} 
                            />
                          </Box>
                        )}
                        <Typography variant="body2">
                          {item.step}
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        {item.time}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Box>
        </Box>
      </Container>
    </Box>
  );
};

export default ValidationPage;
