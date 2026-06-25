import React, { useState } from 'react';
import { Box, Typography, Paper, Grid, Switch, FormControlLabel, Button, Select, MenuItem, FormControl, InputLabel, Alert, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Slider } from '@mui/material';
import { Save, FindInPage } from '@mui/icons-material';

const selectorTypes = [
  { type: 'CSS Selector', example: 'input[name="part_name"]', framework: 'Universal' },
  { type: 'Shadow CSS', example: 'lightning-input >>> input', framework: 'Salesforce LWC' },
  { type: 'XPath', example: '//input[@name="part_name"]', framework: 'Universal' },
  { type: 'Relative XPath', example: '//label[text()="Part Name"]/following::input', framework: 'Universal' },
  { type: 'data-testid', example: '[data-testid="part-name-input"]', framework: 'React' },
  { type: 'formControlName', example: '[formControlName="partName"]', framework: 'Angular' },
];

export default function SelectorsHub() {
  const [config, setConfig] = useState({
    enabled: true, autoScan: true, shadowDom: true, iframeSupport: false,
    scanDepth: 5, priority: 'css'
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>SelectorsHub Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure SelectorsHub integration for automated page element scanning and selector generation.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>SelectorsHub configuration saved!</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControlLabel control={<Switch checked={config.enabled} onChange={e => setConfig({...config, enabled: e.target.checked})} />}
              label="Enable SelectorsHub" />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel control={<Switch checked={config.autoScan} onChange={e => setConfig({...config, autoScan: e.target.checked})} />}
              label="Auto-scan on Execute" />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel control={<Switch checked={config.shadowDom} onChange={e => setConfig({...config, shadowDom: e.target.checked})} />}
              label="Shadow DOM Support" />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControlLabel control={<Switch checked={config.iframeSupport} onChange={e => setConfig({...config, iframeSupport: e.target.checked})} />}
              label="iFrame Support" />
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>Scan Depth: {config.scanDepth}</Typography>
            <Slider value={config.scanDepth} min={1} max={10} marks
              onChange={(_, v) => setConfig({...config, scanDepth: v as number})} />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Selector Priority</InputLabel>
              <Select value={config.priority} label="Selector Priority"
                onChange={e => setConfig({...config, priority: e.target.value})}>
                <MenuItem value="css">CSS First</MenuItem>
                <MenuItem value="xpath">XPath First</MenuItem>
                <MenuItem value="testid">data-testid First</MenuItem>
                <MenuItem value="shadow">Shadow CSS First</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12}>
            <Button variant="contained" startIcon={<Save />} onClick={handleSave} sx={{ mr: 1 }}>Save Configuration</Button>
            <Button variant="outlined" startIcon={<FindInPage />}>Run Manual Scan</Button>
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>Scan → Discover → Generate → Inject</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
          {['Scan App Screens', 'Discover Elements', 'Generate Selectors', 'Inject into POM'].map((step, i) => (
            <React.Fragment key={step}>
              <Chip label={`${i + 1}. ${step}`} color="primary" variant={i < 3 ? 'outlined' : 'filled'} />
              {i < 3 && <Typography color="text.secondary">→</Typography>}
            </React.Fragment>
          ))}
        </Box>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>Supported Selector Types</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Type</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Example</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Framework</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {selectorTypes.map(s => (
              <TableRow key={s.type} hover>
                <TableCell sx={{ fontWeight: 500 }}>{s.type}</TableCell>
                <TableCell><code style={{ fontSize: 12 }}>{s.example}</code></TableCell>
                <TableCell><Chip label={s.framework} size="small" variant="outlined" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
