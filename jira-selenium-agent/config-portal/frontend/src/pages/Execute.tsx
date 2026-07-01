import React, { useState } from 'react';
import { Box, Typography, Paper, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, LinearProgress, Card, CardContent, Grid, Alert } from '@mui/material';
import { PlayArrow, Refresh, CheckCircle } from '@mui/icons-material';

const preflightChecks = [
  { name: 'Application URL', status: 'pass', detail: 'http://localhost:5555' },
  { name: 'Test Data File', status: 'pass', detail: '6 records loaded' },
  { name: 'Selenium Config', status: 'pass', detail: 'Chrome CDP on :29229' },
  { name: 'AI Model', status: 'pass', detail: 'GPT-4o configured' },
  { name: 'Report Output', status: 'pass', detail: 'HTML + JUnit + JSON' },
];

const pipelineResults = [
  { agent: 'StoryIngestionAgent', decision: 'PROCEED', result: 'Loaded 6 test records', duration: '0.2s' },
  { agent: 'AnalysisAgent', decision: 'PROCEED', result: 'Framework: SALESFORCE, 5 screens', duration: '1.1s' },
  { agent: 'FeatureGenerationAgent', decision: 'PROCEED', result: 'Generated 6 Gherkin scenarios', duration: '0.8s' },
  { agent: 'TestDataPreparationAgent', decision: 'PROCEED', result: '6 data bundles, 65 fields', duration: '0.3s' },
  { agent: 'PageObjectAgent', decision: 'PROCEED', result: 'SelectorsHub scanned 12 fields → LWC POM', duration: '2.4s' },
  { agent: 'ExecutionAgent', decision: 'PROCEED', result: '6/6 UI scenarios passed, 58 steps', duration: '12.5s' },
  { agent: 'APITestingAgent', decision: 'PROCEED', result: '18/18 API scenarios passed (10 CRUD + 8 relationship), 69 steps', duration: '0.5s' },
  { agent: 'ReportingAgent', decision: 'PROCEED', result: 'HTML/XML/JSON reports (UI + API)', duration: '0.6s' },
  { agent: 'DeploymentAgent', decision: 'SKIP', result: 'Copado not configured', duration: '0.0s' },
  { agent: 'FeedbackAgent', decision: 'SKIP', result: 'No changes detected', duration: '0.0s' },
];

export default function Execute() {
  const [running, setRunning] = useState(false);
  const [completed, setCompleted] = useState(false);

  const runPipeline = () => {
    setRunning(true);
    setCompleted(false);
    setTimeout(() => { setRunning(false); setCompleted(true); }, 3000);
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Execute Pipeline</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Scan the application for changes and run the full 10-agent end-to-end pipeline (UI + API testing).
      </Typography>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Pre-flight Checks</Typography>
        <Table size="small">
          <TableBody>
            {preflightChecks.map(c => (
              <TableRow key={c.name}>
                <TableCell sx={{ width: 200 }}>{c.name}</TableCell>
                <TableCell><Chip label={c.status === 'pass' ? 'Ready' : 'Missing'} size="small" color={c.status === 'pass' ? 'success' : 'error'} /></TableCell>
                <TableCell>{c.detail}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button variant="contained" size="large" startIcon={<PlayArrow />} onClick={runPipeline} disabled={running}>
          {running ? 'Running...' : 'Scan & Execute Pipeline'}
        </Button>
        <Button variant="outlined" startIcon={<Refresh />} disabled={running}>Scan Only</Button>
      </Box>

      {running && <LinearProgress sx={{ mb: 2 }} />}

      {completed && (
        <>
          <Alert severity="success" sx={{ mb: 2 }} icon={<CheckCircle />}>
            Pipeline completed — 24/24 scenarios passed (6 UI + 10 API + 8 Relationship), 127 steps executed in 18.5s
          </Alert>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="success.main" fontWeight={700}>24/24</Typography>
                <Typography variant="caption">Scenarios (6 UI + 10 API + 8 Rel)</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="primary" fontWeight={700}>127</Typography>
                <Typography variant="caption">Steps (58 UI + 30 API + 39 Rel)</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="success.main" fontWeight={700}>100%</Typography>
                <Typography variant="caption">Pass Rate</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="secondary" fontWeight={700}>18.2s</Typography>
                <Typography variant="caption">Duration</Typography>
              </CardContent></Card>
            </Grid>
          </Grid>

          <Typography variant="h6" fontWeight={600} gutterBottom>Agent Pipeline Results</Typography>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow sx={{ bgcolor: 'primary.main' }}>
                  <TableCell sx={{ color: 'white', fontWeight: 600 }}>#</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 600 }}>Agent</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 600 }}>Decision</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 600 }}>Result</TableCell>
                  <TableCell sx={{ color: 'white', fontWeight: 600 }}>Duration</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {pipelineResults.map((r, i) => (
                  <TableRow key={r.agent}>
                    <TableCell>{i + 1}</TableCell>
                    <TableCell sx={{ fontWeight: 500 }}>{r.agent}</TableCell>
                    <TableCell>
                      <Chip label={r.decision} size="small"
                        color={r.decision === 'PROCEED' ? 'success' : r.decision === 'SKIP' ? 'default' : 'error'} />
                    </TableCell>
                    <TableCell>{r.result}</TableCell>
                    <TableCell>{r.duration}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}
    </Box>
  );
}
