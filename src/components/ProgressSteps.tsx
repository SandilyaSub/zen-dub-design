
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
      mb: 4, 
      px: 2,
      pt: 3, // Consistent top padding
      pb: 2  // Consistent bottom padding
    }}>
      <Stepper activeStep={getActiveStep()} alternativeLabel>
        {steps.map((step) => (
          <Step key={step.key}>
            <StepLabel>
              <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.875rem' }}>
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
