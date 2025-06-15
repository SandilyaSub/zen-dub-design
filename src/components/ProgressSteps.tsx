
import { Box, Typography, Stepper, Step, StepLabel } from '@mui/material';
import { useSession } from '../context/SessionContext';

const steps = [
  { label: 'Input', key: 'input' },
  { label: 'Transcription', key: 'transcription' },
  { label: 'Translation', key: 'translation' },
  { label: 'Speech Synthesis', key: 'synthesis' },
  { label: 'Validation', key: 'validation' }
];

const ProgressSteps = () => {
  const { currentStep } = useSession();
  
  const getActiveStep = () => {
    switch (currentStep) {
      case 'input': return 0;
      case 'transcription': return 1;
      case 'translation': return 2;
      case 'synthesis': return 3;
      case 'validation': return 4;
      default: return 0;
    }
  };

  return (
    <Box sx={{ 
      width: '100%', 
      maxWidth: '1000px',
      mx: 'auto',
      mb: 4,
      px: { xs: 2, md: 3 },
      mt: 3
    }}>
      <Stepper activeStep={getActiveStep()} alternativeLabel>
        {steps.map((step) => (
          <Step key={step.key}>
            <StepLabel>
              <Typography variant="body2" sx={{ 
                fontWeight: 500, 
                fontSize: '0.875rem',
                color: 'text.primary'
              }}>
                {step.label}
              </Typography>
            </StepLabel>
          </Step>
        ))}
      </Stepper>
    </Box>
  );
};

export default ProgressSteps;
