
import { useState } from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Collapse,
  IconButton
} from '@mui/material';
import { CheckCircle, ExpandMore, ExpandLess } from '@mui/icons-material';

const AdvancedFeatures = () => {
  const [expanded, setExpanded] = useState(false);

  const handleExpandClick = () => {
    setExpanded(!expanded);
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <CheckCircle sx={{ mr: 1, color: '#10b981', fontSize: 20 }} />
            Advanced Features
          </Typography>
          <IconButton
            onClick={handleExpandClick}
            aria-expanded={expanded}
            aria-label="show more"
            size="small"
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </IconButton>
        </Box>
        
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Powered by state-of-the-art AI models for professional-grade results:
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#6366f1', mr: 2 }} />
                Speaker identification & separation
              </Typography>
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#6366f1', mr: 2 }} />
                Smart audio segmentation
              </Typography>
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#6366f1', mr: 2 }} />
                Multi-format audio support
              </Typography>
              <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center' }}>
                <Box sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: '#6366f1', mr: 2 }} />
                Video-to-audio extraction
              </Typography>
            </Box>
          </Box>
        </Collapse>
      </CardContent>
    </Card>
  );
};

export default AdvancedFeatures;
