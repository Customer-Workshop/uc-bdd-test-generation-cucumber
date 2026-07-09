import React, { useState } from 'react';
import { Box, Typography, Paper, Button, TextField, Alert, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Tabs, Tab, CircularProgress } from '@mui/material';
import { Upload, ContentPaste, CheckCircle, AutoAwesome } from '@mui/icons-material';

const sampleJson = `[
  {
    "jira_id": "CAR-1001",
    "test_case": "TC-001",
    "name": "Create Engine Component",
    "fields": {
      "part_name": "Turbocharger Assembly",
      "part_category": "Engine Components",
      "manufacturer": "BorgWarner"
    }
  }
]`;

export default function UploadTestData() {
  const [tab, setTab] = useState(0);

  // Manual upload state
  const [jsonText, setJsonText] = useState('');
  const [uploaded, setUploaded] = useState(false);
  const [error, setError] = useState('');

  // AI generation state
  const [appUrl, setAppUrl] = useState('http://localhost:5555');
  const [count, setCount] = useState(6);
  const [generating, setGenerating] = useState(false);
  const [genResult, setGenResult] = useState<any>(null);
  const [genError, setGenError] = useState('');
  const [genSaved, setGenSaved] = useState(false);

  const validateJson = () => {
    try { JSON.parse(jsonText); setError(''); return true; } catch (e: any) { setError(e.message); return false; }
  };

  const handleUpload = () => {
    if (validateJson()) { setUploaded(true); setTimeout(() => setUploaded(false), 3000); }
  };

  const parseJson = async (resp: Response) => {
    const text = await resp.text();
    try { return text ? JSON.parse(text) : {}; }
    catch { throw new Error(`Server returned an invalid response (HTTP ${resp.status}).`); }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setGenResult(null);
    setGenError('');
    setGenSaved(false);
    try {
      const resp = await fetch('/api/test-data/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: appUrl, count }),
      });
      const data = await parseJson(resp);
      if (data.error) { setGenError(data.error); } else { setGenResult(data); }
    } catch (err) {
      setGenError(err instanceof Error ? err.message : String(err));
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveGenerated = async () => {
    if (!genResult?.data) return;
    try {
      const resp = await fetch('/api/test-data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(genResult.data),
      });
      await parseJson(resp);
      setGenSaved(true);
      setTimeout(() => setGenSaved(false), 3000);
    } catch (err) {
      setGenError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Test Data</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Provide test data for Selenium BDD execution — either upload a JSON file manually or generate it with AI from the scanned application fields.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Current Test Data File</Typography>
        <Table size="small">
          <TableBody>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>File Path</TableCell><TableCell><code>car_parts_test_data.json</code></TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Status</TableCell><TableCell><Chip label="File Exists" size="small" color="success" /></TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Records</TableCell><TableCell>6 test scenarios</TableCell></TableRow>
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab icon={<Upload />} iconPosition="start" label="Manual Upload" />
          <Tab icon={<AutoAwesome />} iconPosition="start" label="AI-Generated" />
        </Tabs>

        {tab === 0 && (
          <Box sx={{ p: 3 }}>
            {uploaded && <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>Test data uploaded successfully! 6 records loaded.</Alert>}
            {error && <Alert severity="error" sx={{ mb: 2 }}>Invalid JSON: {error}</Alert>}

            <Paper variant="outlined" sx={{ p: 3, mb: 3, border: '2px dashed', borderColor: 'primary.main', textAlign: 'center', cursor: 'pointer' }}>
              <Upload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
              <Typography variant="subtitle1" fontWeight={600}>Drag & Drop JSON File Here</Typography>
              <Typography variant="caption" color="text.secondary">or click to browse (max 5MB, .json format)</Typography>
            </Paper>

            <Typography variant="subtitle2" fontWeight={600} gutterBottom>Paste JSON</Typography>
            <TextField fullWidth multiline rows={8} placeholder="Paste your test data JSON here..."
              value={jsonText} onChange={e => setJsonText(e.target.value)}
              sx={{ mb: 2, fontFamily: 'monospace', '& textarea': { fontFamily: 'monospace', fontSize: 12 } }} />
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button variant="outlined" onClick={validateJson}>Validate JSON</Button>
              <Button variant="outlined" onClick={() => setJsonText(JSON.stringify(JSON.parse(jsonText || '[]'), null, 2))}>Format</Button>
              <Button variant="outlined" startIcon={<ContentPaste />} onClick={() => setJsonText(sampleJson)}>Load Sample</Button>
              <Button variant="contained" startIcon={<Upload />} onClick={handleUpload}>Upload</Button>
            </Box>
          </Box>
        )}

        {tab === 1 && (
          <Box sx={{ p: 3 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              The AI model scans the target application's fields and synthesizes test data scenarios from the discovered picklist values.
            </Typography>
            {genSaved && <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>Generated test data saved to the test data file.</Alert>}
            {genError && <Alert severity="error" sx={{ mb: 2 }}>{genError}</Alert>}

            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 2, flexWrap: 'wrap' }}>
              <TextField label="Application URL" size="small" sx={{ flex: 1, minWidth: 260 }}
                value={appUrl} onChange={e => setAppUrl(e.target.value)} />
              <TextField label="Scenarios" size="small" type="number" sx={{ width: 120 }}
                value={count} onChange={e => setCount(Math.max(1, parseInt(e.target.value || '1', 10)))} />
              <Button variant="contained" startIcon={generating ? <CircularProgress size={16} color="inherit" /> : <AutoAwesome />}
                onClick={handleGenerate} disabled={generating}>
                {generating ? 'Generating...' : 'Generate with AI'}
              </Button>
            </Box>

            {genResult && (
              <Paper variant="outlined" sx={{ p: 2 }}>
                <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                  <Chip label={`${genResult.records} scenarios`} color="primary" size="small" />
                  <Chip label={`Model: ${genResult.model}`} size="small" />
                  <Chip label={`${genResult.fields_used?.length || 0} fields used`} size="small" />
                  <Chip
                    label={genResult.generation_mode === 'llm' ? 'Live LLM' : 'Synthesis (no key)'}
                    color={genResult.generation_mode === 'llm' ? 'success' : 'default'}
                    size="small"
                  />
                  <Box sx={{ flex: 1 }} />
                  <Button variant="outlined" size="small" startIcon={<CheckCircle />} onClick={handleSaveGenerated}>
                    Save as Test Data
                  </Button>
                </Box>
                {genResult.warning && <Alert severity="warning" sx={{ mb: 2 }}>{genResult.warning}</Alert>}
                <TableContainer sx={{ maxHeight: 260, mb: 2 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>Jira ID</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Test Case</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Name</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Fields</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {genResult.data?.map((r: any) => (
                        <TableRow key={r.jira_id}>
                          <TableCell><code>{r.jira_id}</code></TableCell>
                          <TableCell>{r.test_case}</TableCell>
                          <TableCell>{r.name}</TableCell>
                          <TableCell>{Object.keys(r.fields || {}).length}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                <TextField fullWidth multiline rows={8} value={JSON.stringify(genResult.data, null, 2)}
                  InputProps={{ readOnly: true }}
                  sx={{ fontFamily: 'monospace', '& textarea': { fontFamily: 'monospace', fontSize: 12 } }} />
              </Paper>
            )}
          </Box>
        )}
      </Paper>
    </Box>
  );
}
