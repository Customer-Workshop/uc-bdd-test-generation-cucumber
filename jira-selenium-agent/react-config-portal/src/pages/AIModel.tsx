import React, { useState } from 'react';
import { Box, Typography, Paper, TextField, Button, Grid, Switch, FormControlLabel, Select, MenuItem, FormControl, InputLabel, Alert, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { Save } from '@mui/icons-material';

const models: Record<string, string[]> = {
  'OpenAI': ['GPT-4o', 'GPT-4o Mini', 'GPT-4 Turbo', 'GPT-3.5 Turbo'],
  'Azure OpenAI': ['GPT-4o (Azure)', 'GPT-4 (Azure)'],
  'Anthropic': ['Claude 3.5 Sonnet', 'Claude 3 Opus', 'Claude 3 Haiku'],
  'Google': ['Gemini 1.5 Pro', 'Gemini 1.5 Flash'],
  'Local': ['Ollama (Llama 3)', 'Ollama (Mistral)'],
};

const autoActions = [
  { trigger: 'New Field Added', action: 'Add field to POM locators + update test scenarios + update test data', agents: 'Analysis → POM → Feature → Data' },
  { trigger: 'New Screen Added', action: 'Generate new page object + create test scenarios + add navigation steps', agents: 'Analysis → POM → Feature' },
  { trigger: 'Field Modified', action: 'Update existing locators + modify affected test steps', agents: 'POM → Feature' },
  { trigger: 'Git Commit Detected', action: 'Analyze diff → identify UI changes → auto-update features', agents: 'Feedback → Feature' },
  { trigger: 'Test Failure', action: 'Analyze failure → suggest fix → retry with updated POM', agents: 'Execution → POM → Retry' },
  { trigger: 'Jira Story Updated', action: 'Re-generate affected feature files from updated acceptance criteria', agents: 'Ingestion → Feature' },
];

export default function AIModel() {
  const [config, setConfig] = useState({
    provider: 'OpenAI', model: 'GPT-4o', temperature: '0.3', maxTokens: '4096', apiKey: '',
    autoNewFields: true, autoNewScreens: true, autoUpdateTests: true,
    autoUpdatePom: true, autoUpdateReports: true, gitDiffAnalysis: true
  });
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>AI Model Configuration</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Configure the LLM model for automated test case generation, maintenance, and auto-update on application changes.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>AI Model configuration saved!</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>Model Settings</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Provider</InputLabel>
              <Select value={config.provider} label="Provider"
                onChange={e => setConfig({...config, provider: e.target.value, model: models[e.target.value][0]})}>
                {Object.keys(models).map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Model</InputLabel>
              <Select value={config.model} label="Model"
                onChange={e => setConfig({...config, model: e.target.value})}>
                {(models[config.provider] || []).map(m => <MenuItem key={m} value={m}>{m}</MenuItem>)}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth label="Temperature" type="number" inputProps={{ step: 0.1, min: 0, max: 2 }}
              value={config.temperature} onChange={e => setConfig({...config, temperature: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth label="Max Tokens" type="number"
              value={config.maxTokens} onChange={e => setConfig({...config, maxTokens: e.target.value})} />
          </Grid>
          <Grid item xs={12} sm={4}>
            <TextField fullWidth label="API Key" type="password"
              value={config.apiKey} onChange={e => setConfig({...config, apiKey: e.target.value})} />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>Auto-Detection Toggles</Typography>
        <Grid container spacing={1}>
          <Grid item xs={12} sm={6}><FormControlLabel control={<Switch checked={config.autoNewFields} onChange={e => setConfig({...config, autoNewFields: e.target.checked})} />} label="Detect New Fields" /></Grid>
          <Grid item xs={12} sm={6}><FormControlLabel control={<Switch checked={config.autoNewScreens} onChange={e => setConfig({...config, autoNewScreens: e.target.checked})} />} label="Detect New Screens" /></Grid>
          <Grid item xs={12} sm={6}><FormControlLabel control={<Switch checked={config.autoUpdateTests} onChange={e => setConfig({...config, autoUpdateTests: e.target.checked})} />} label="Auto-Update Test Cases" /></Grid>
          <Grid item xs={12} sm={6}><FormControlLabel control={<Switch checked={config.autoUpdatePom} onChange={e => setConfig({...config, autoUpdatePom: e.target.checked})} />} label="Auto-Update Page Objects" /></Grid>
          <Grid item xs={12} sm={6}><FormControlLabel control={<Switch checked={config.autoUpdateReports} onChange={e => setConfig({...config, autoUpdateReports: e.target.checked})} />} label="Auto-Update Reports" /></Grid>
          <Grid item xs={12} sm={6}><FormControlLabel control={<Switch checked={config.gitDiffAnalysis} onChange={e => setConfig({...config, gitDiffAnalysis: e.target.checked})} />} label="Git Diff Analysis" /></Grid>
        </Grid>
        <Button variant="contained" startIcon={<Save />} onClick={handleSave} sx={{ mt: 2 }}>Save AI Configuration</Button>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>AI Auto-Update Actions</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'secondary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Trigger</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>AI Action</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Agents Involved</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {autoActions.map(a => (
              <TableRow key={a.trigger} hover>
                <TableCell sx={{ fontWeight: 500 }}>{a.trigger}</TableCell>
                <TableCell>{a.action}</TableCell>
                <TableCell><Typography variant="caption" color="primary">{a.agents}</Typography></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
