import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Switch, FormControlLabel, Alert } from '@mui/material';
import { Save } from '@mui/icons-material';

export default function GitHubConfig() {
  const [config, setConfig] = useState({
    repoUrl: '', branch: 'main', workflowFile: '.github/workflows/bdd-test-agent.yml',
    autoTrigger: false, token: ''
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>GitHub Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure GitHub repository for CI/CD integration and feature file storage.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>GitHub configuration saved!</Alert>}

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField fullWidth label="Repository URL" placeholder="https://github.com/org/repo"
              value={config.repoUrl} onChange={e => setConfig({...config, repoUrl: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Branch" value={config.branch}
              onChange={e => setConfig({...config, branch: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Workflow File" value={config.workflowFile}
              onChange={e => setConfig({...config, workflowFile: e.target.value})} />
          </Grid>
          <Grid item xs={12}>
            <TextField fullWidth label="Personal Access Token" type="password"
              value={config.token} onChange={e => setConfig({...config, token: e.target.value})} />
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel control={<Switch checked={config.autoTrigger} onChange={e => setConfig({...config, autoTrigger: e.target.checked})} />}
              label="Auto-trigger workflow on test completion" />
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" startIcon={<Save />} onClick={handleSave}>Save GitHub Configuration</Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}
