import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Select, MenuItem, FormControl, InputLabel, Alert, Chip, Table, TableBody, TableCell, TableRow, CircularProgress } from '@mui/material';
import { Save, OpenInNew, Search } from '@mui/icons-material';

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
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [scanError, setScanError] = useState('');

  useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(data => {
        if (data.app_url) setAppUrl(data.app_url);
        if (data.ui_framework) setFramework(data.ui_framework);
      })
      .catch(() => {});
  }, []);

  const handleSave = () => {
    fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_url: appUrl, ui_framework: framework }),
    })
      .then(r => r.json())
      .then(() => { setSaved(true); setTimeout(() => setSaved(false), 3000); })
      .catch(() => {});
  };

  const handleScan = async () => {
    setScanning(true);
    setScanResult(null);
    setScanError('');
    try {
      const resp = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: appUrl }),
      });
      const responseText = await resp.text();
      let data: any;
      try {
        data = responseText ? JSON.parse(responseText) : {};
      } catch {
        throw new Error(`Server returned an invalid response (HTTP ${resp.status}). The backend may be down or errored.`);
      }
      if (data.errors && data.errors.length > 0 && !data.reachable) {
        setScanError(data.errors[0]);
      } else {
        setScanResult(data);
      }
    } catch (err) {
      setScanError(err instanceof Error ? err.message : String(err));
    } finally {
      setScanning(false);
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Application URL Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure the target application URL. Click "Scan" to discover screens, API endpoints, and fields.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>Application URL saved!</Alert>}
      {scanError && <Alert severity="error" sx={{ mb: 2 }}>{scanError}</Alert>}

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
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="contained" startIcon={<Save />} onClick={handleSave}>Save Configuration</Button>
              <Button variant="outlined" startIcon={scanning ? <CircularProgress size={16} /> : <Search />} onClick={handleScan} disabled={scanning}>
                {scanning ? 'Scanning...' : 'Scan Application'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {scanResult && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Scan Results
            <Chip label={scanResult.reachable ? 'Reachable' : 'Unreachable'} size="small"
              color={scanResult.reachable ? 'success' : 'error'} sx={{ ml: 1 }} />
            {scanResult.framework_detected !== 'unknown' && (
              <Chip label={scanResult.framework_detected} size="small" color="info" sx={{ ml: 1 }} />
            )}
          </Typography>

          {scanResult.screens && scanResult.screens.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>Screens Discovered ({scanResult.screens.filter((s: any) => s.state === 'active').length} active)</Typography>
              <Table size="small">
                <TableBody>
                  {scanResult.screens.map((s: any) => (
                    <TableRow key={s.path}>
                      <TableCell sx={{ width: 160 }}><code>{s.path}</code></TableCell>
                      <TableCell>{s.label}</TableCell>
                      <TableCell>
                        <Chip label={s.state} size="small"
                          color={s.state === 'active' ? 'success' : s.state === 'missing' ? 'warning' : 'error'} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}

          {scanResult.api_endpoints && scanResult.api_endpoints.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>API Endpoints ({scanResult.api_endpoints.filter((e: any) => e.available).length} available)</Typography>
              <Table size="small">
                <TableBody>
                  {scanResult.api_endpoints.map((ep: any) => (
                    <TableRow key={ep.path}>
                      <TableCell sx={{ width: 80 }}>
                        <Chip label={ep.method} size="small"
                          color={ep.method === 'GET' ? 'success' : ep.method === 'POST' ? 'primary' : 'warning'} />
                      </TableCell>
                      <TableCell><code>{ep.path}</code></TableCell>
                      <TableCell>{ep.description}</TableCell>
                      <TableCell>
                        <Chip label={ep.available ? 'OK' : ep.status || 'N/A'} size="small"
                          color={ep.available ? 'success' : 'error'} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}

          {scanResult.fields && scanResult.fields.length > 0 && (
            <Box>
              <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>Fields Discovered ({scanResult.field_count})</Typography>
              <Table size="small">
                <TableBody>
                  {scanResult.fields.map((f: any, i: number) => (
                    <TableRow key={i}>
                      <TableCell><code>{f.api_name}</code></TableCell>
                      <TableCell>{f.label}</TableCell>
                      <TableCell>{f.type}</TableCell>
                      <TableCell>{f.required ? <Chip label="Required" size="small" color="error" /> : ''}</TableCell>
                      <TableCell>{f.values_count} values</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </Paper>
      )}

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
