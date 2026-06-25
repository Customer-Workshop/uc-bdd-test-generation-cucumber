import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Switch, FormControlLabel, Select, MenuItem, FormControl, InputLabel, Alert } from '@mui/material';
import { Save } from '@mui/icons-material';

export default function SeleniumConfig() {
  const [config, setConfig] = useState({
    browser: 'chrome', cdpUrl: 'http://localhost:29229', headless: false,
    timeout: '30', screenshotOnFail: true, windowWidth: '1920', windowHeight: '1080'
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Selenium Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure Selenium WebDriver settings for test execution.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>Selenium configuration saved!</Alert>}

      <Paper sx={{ p: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Browser</InputLabel>
              <Select value={config.browser} label="Browser"
                onChange={e => setConfig({...config, browser: e.target.value})}>
                <MenuItem value="chrome">Chrome</MenuItem>
                <MenuItem value="firefox">Firefox</MenuItem>
                <MenuItem value="edge">Edge</MenuItem>
                <MenuItem value="safari">Safari</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <TextField fullWidth label="CDP URL" placeholder="http://localhost:29229"
              value={config.cdpUrl} onChange={e => setConfig({...config, cdpUrl: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth label="Timeout (seconds)" type="number"
              value={config.timeout} onChange={e => setConfig({...config, timeout: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth label="Window Width" type="number"
              value={config.windowWidth} onChange={e => setConfig({...config, windowWidth: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth label="Window Height" type="number"
              value={config.windowHeight} onChange={e => setConfig({...config, windowHeight: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel control={<Switch checked={config.headless} onChange={e => setConfig({...config, headless: e.target.checked})} />}
              label="Headless Mode" />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel control={<Switch checked={config.screenshotOnFail} onChange={e => setConfig({...config, screenshotOnFail: e.target.checked})} />}
              label="Screenshot on Failure" />
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" startIcon={<Save />} onClick={handleSave}>Save Selenium Configuration</Button>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}
