import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Switch, FormControlLabel, Select, MenuItem, FormControl, InputLabel, Alert } from '@mui/material';
import { Save } from '@mui/icons-material';

export default function JiraConfig() {
  const [config, setConfig] = useState({
    serverUrl: '', username: '', apiToken: '', projectKey: 'CAR',
    storyStatus: 'Ready for Testing', autoFetch: false
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Jira Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Connect to Jira to auto-fetch user stories for BDD test generation.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>Jira configuration saved!</Alert>}

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField fullWidth label="Jira Server URL" placeholder="https://your-org.atlassian.net"
              value={config.serverUrl} onChange={e => setConfig({...config, serverUrl: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Username / Email" placeholder="user@company.com"
              value={config.username} onChange={e => setConfig({...config, username: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="API Token" type="password" placeholder="Enter Jira API token"
              value={config.apiToken} onChange={e => setConfig({...config, apiToken: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="Project Key" placeholder="CAR"
              value={config.projectKey} onChange={e => setConfig({...config, projectKey: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Story Status Filter</InputLabel>
              <Select value={config.storyStatus} label="Story Status Filter"
                onChange={e => setConfig({...config, storyStatus: e.target.value})}>
                <MenuItem value="To Do">To Do</MenuItem>
                <MenuItem value="In Progress">In Progress</MenuItem>
                <MenuItem value="Ready for Testing">Ready for Testing</MenuItem>
                <MenuItem value="Done">Done</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <FormControlLabel control={<Switch checked={config.autoFetch} onChange={e => setConfig({...config, autoFetch: e.target.checked})} />}
              label="Auto-fetch stories on pipeline execution" />
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" startIcon={<Save />} onClick={handleSave}>Save Jira Configuration</Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}
