import React, { useState } from 'react';
import { Box, Typography, Paper, Button, TextField, Alert, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { Upload, ContentPaste, CheckCircle } from '@mui/icons-material';

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
  const [jsonText, setJsonText] = useState('');
  const [uploaded, setUploaded] = useState(false);
  const [error, setError] = useState('');

  const validateJson = () => {
    try { JSON.parse(jsonText); setError(''); return true; } catch (e: any) { setError(e.message); return false; }
  };

  const handleUpload = () => {
    if (validateJson()) { setUploaded(true); setTimeout(() => setUploaded(false), 3000); }
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Upload Test Data</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Upload JSON test data file for Selenium BDD test execution.
      </Typography>

      {uploaded && <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>Test data uploaded successfully! 6 records loaded.</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>Invalid JSON: {error}</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Current Test Data File</Typography>
        <Table size="small" sx={{ mb: 2 }}>
          <TableBody>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>File Path</TableCell><TableCell><code>car_parts_test_data.json</code></TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Status</TableCell><TableCell><Chip label="File Exists" size="small" color="success" /></TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Records</TableCell><TableCell>6 test scenarios</TableCell></TableRow>
            <TableRow><TableCell sx={{ fontWeight: 600 }}>Size</TableCell><TableCell>7.2 KB</TableCell></TableRow>
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ p: 3, mb: 3, border: '2px dashed', borderColor: 'primary.main', textAlign: 'center', cursor: 'pointer' }}>
        <Upload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
        <Typography variant="subtitle1" fontWeight={600}>Drag & Drop JSON File Here</Typography>
        <Typography variant="caption" color="text.secondary">or click to browse (max 5MB, .json format)</Typography>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Paste JSON</Typography>
        <TextField fullWidth multiline rows={8} placeholder="Paste your test data JSON here..."
          value={jsonText} onChange={e => setJsonText(e.target.value)}
          sx={{ mb: 2, fontFamily: 'monospace', '& textarea': { fontFamily: 'monospace', fontSize: 12 } }} />
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" onClick={validateJson}>Validate JSON</Button>
          <Button variant="outlined" onClick={() => setJsonText(JSON.stringify(JSON.parse(jsonText || '[]'), null, 2))}>Format</Button>
          <Button variant="outlined" startIcon={<ContentPaste />} onClick={() => setJsonText(sampleJson)}>Load Sample</Button>
          <Button variant="contained" startIcon={<Upload />} onClick={handleUpload}>Upload</Button>
        </Box>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Upload History</Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Timestamp</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Source</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Records</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>2024-01-15 10:30:00</TableCell>
                <TableCell>car_parts_test_data.json</TableCell>
                <TableCell>6</TableCell>
                <TableCell><Chip label="Active" size="small" color="success" /></TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}
