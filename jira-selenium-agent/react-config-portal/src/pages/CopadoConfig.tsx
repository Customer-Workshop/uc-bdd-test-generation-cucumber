import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Switch, FormControlLabel, Select, MenuItem, FormControl, InputLabel, Alert, Stepper, Step, StepLabel } from '@mui/material';
import { Save } from '@mui/icons-material';

const environments = ['DEV', 'SIT', 'UAT', 'STAGING', 'PRODUCTION'];
const pipelineStages = ['Create Test Run', 'Upload Results', 'Attach Reports', 'Validate Pipeline', 'Trigger Deployment', 'Verify Promotion'];

export default function CopadoConfig() {
  const [config, setConfig] = useState({
    enabled: false, instanceUrl: '', apiToken: '', pipelineId: '',
    targetEnv: 'UAT', deployOnPass: true
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Copado CI/CD Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure Copado deployment for automated CI/CD pipeline execution.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>Copado configuration saved!</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <FormControlLabel control={<Switch checked={config.enabled} onChange={e => setConfig({...config, enabled: e.target.checked})} />}
          label="Enable Copado Deployment" />
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12}>
            <TextField fullWidth label="Copado Instance URL" placeholder="https://your-org.copado.com"
              value={config.instanceUrl} onChange={e => setConfig({...config, instanceUrl: e.target.value})} disabled={!config.enabled} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="API Token" type="password"
              value={config.apiToken} onChange={e => setConfig({...config, apiToken: e.target.value})} disabled={!config.enabled} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Pipeline ID"
              value={config.pipelineId} onChange={e => setConfig({...config, pipelineId: e.target.value})} disabled={!config.enabled} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth disabled={!config.enabled}>
              <InputLabel>Target Environment</InputLabel>
              <Select value={config.targetEnv} label="Target Environment"
                onChange={e => setConfig({...config, targetEnv: e.target.value})}>
                {environments.map(env => <MenuItem key={env} value={env}>{env}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel control={<Switch checked={config.deployOnPass} onChange={e => setConfig({...config, deployOnPass: e.target.checked})} disabled={!config.enabled} />}
              label="Deploy only on 100% pass rate" />
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" startIcon={<Save />} onClick={handleSave}>Save Copado Configuration</Button>
          </Grid>
        </Grid>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>Copado Pipeline Stages</Typography>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper alternativeLabel>
          {pipelineStages.map(stage => (
            <Step key={stage} completed={false}>
              <StepLabel>{stage}</StepLabel>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>Environment Promotion Path</Typography>
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, flexWrap: 'wrap' }}>
          {environments.map((env, i) => (
            <React.Fragment key={env}>
              <Box sx={{ px: 2, py: 1, bgcolor: config.targetEnv === env ? 'primary.main' : 'grey.200', color: config.targetEnv === env ? 'white' : 'text.primary', borderRadius: 1, fontWeight: 600, fontSize: 13 }}>
                {env}
              </Box>
              {i < environments.length - 1 && <Typography color="text.secondary">→</Typography>}
            </React.Fragment>
          ))}
        </Box>
      </Paper>
    </Box>
  );
}
