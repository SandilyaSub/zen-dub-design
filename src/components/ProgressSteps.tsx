
import { Box, Typography, Stepper, Step, StepLabel } from '@mui/material';
import { useSession } from '../context/SessionContext';

const steps = [
  { label: 'Input', key: 'input' },
  { label: 'Transcription', key: 'transcription' },
  { label: 'Transliteration', key: 'transliteration' },
  { label: 'Translation', key: 'translation' },
  { label: 'Synthesis', key: 'synthesis' }
];

const ProgressSteps = () => {
  const { currentStep } = useSession();
  
  const getActiveStep = () => {
    switch (currentStep) {
      case 'input': return 0;
      case 'transcription': return 1;
      case 'transliteration': return 2;
      case 'translation': return 3;
      case 'synthesis': return 4;
      default: return 0;
    }
  };

  return (
    <Box sx={{ width: '100%', mb: 4 }}>
      <Stepper activeStep={getActiveStep()} alternativeLabel>
        {steps.map((step) => (
          <Step key={step.key}>
            <StepLabel>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
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
