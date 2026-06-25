import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Select, MenuItem, FormControl, InputLabel, Alert, Chip, Table, TableBody, TableCell, TableRow } from '@mui/material';
import { Save, OpenInNew } from '@mui/icons-material';

const quickUrls = [
  { label: 'Mock Salesforce', url: 'http://localhost:5555' },
  { label: 'Salesforce Production', url: 'https://login.salesforce.com' },
  { label: 'Salesforce Sandbox', url: 'https://test.salesforce.com' },
  { label: 'React App', url: 'http://localhost:3000' },
  { label: 'Angular App', url: 'http://localhost:4200' },
];

export default function AppConfigure() {
  const [appUrl, setAppUrl] = useState('http://localhost:5555');
  const [framework, setFramework] = useState('salesforce');
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Application URL Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure the target application URL for Selenium test execution.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>Application URL saved!</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField fullWidth label="Target Application URL" value={appUrl}
              onChange={e => setAppUrl(e.target.value)}
              InputProps={{ endAdornment: <Button size="small" startIcon={<OpenInNew />} href={appUrl} target="_blank">Open</Button> }} />
          </Grid>
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {quickUrls.map(q => (
                <Chip key={q.label} label={q.label} onClick={() => setAppUrl(q.url)}
                  color={appUrl === q.url ? 'primary' : 'default'} variant={appUrl === q.url ? 'filled' : 'outlined'} />
              ))}
            </Box>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>UI Framework</InputLabel>
              <Select value={framework} label="UI Framework" onChange={e => setFramework(e.target.value)}>
                <MenuItem value="salesforce">Salesforce LWC (Shadow DOM)</MenuItem>
                <MenuItem value="react">React (data-testid)</MenuItem>
                <MenuItem value="angular">Angular (formControlName)</MenuItem>
                <MenuItem value="auto">Auto-Detect</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" startIcon={<Save />} onClick={handleSave}>Save Configuration</Button>
          </Grid>
        </Grid>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>Current Selenium Target</Typography>
      <Paper sx={{ p: 2 }}>
        <Table size="small">
          <TableBody>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Base URL</TableCell><TableCell>{appUrl}</TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Login Page</TableCell><TableCell>{appUrl}/</TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>UI Framework</TableCell><TableCell>{framework === 'salesforce' ? 'Salesforce LWC' : framework === 'react' ? 'React' : framework === 'angular' ? 'Angular' : 'Auto-Detect'}</TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Browser</TableCell><TableCell>Chrome (CDP)</TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Selector Strategy</TableCell><TableCell>{framework === 'salesforce' ? 'Shadow DOM CSS (>>>)' : framework === 'react' ? 'data-testid attributes' : framework === 'angular' ? 'formControlName' : 'Auto'}</TableCell></TableRow>
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
