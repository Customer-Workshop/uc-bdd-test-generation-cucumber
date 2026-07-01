import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Chip, LinearProgress, Card, CardContent, Grid, Alert, TextField } from '@mui/material';
import { PlayArrow, CheckCircle, Error as ErrorIcon, Search } from '@mui/icons-material';

interface ScanResult {
  url: string;
  reachable: boolean;
  status_code: number | null;
  screens: { path: string; label: string; status: number; state: string }[];
  api_endpoints: { path: string; method: string; description: string; status: number; available: boolean }[];
  fields: { api_name: string; label: string; type: string; required: boolean; values_count: number }[];
  field_count: number;
  framework_detected: string;
  errors: string[];
  timestamp: string;
}

interface PipelineResult {
  run_id: string;
  status: string;
  app_url?: string;
  app_reachable?: boolean;
  fields_discovered?: number;
  scenarios_passed: number;
  scenarios_total: number;
  steps?: number;
  duration?: string;
  error?: string;
  agents?: { name: string; decision: string; result: string }[];
}

export default function Execute() {
  const [appUrl, setAppUrl] = useState('http://localhost:5555');
  const [scanning, setScanning] = useState(false);
  const [running, setRunning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [pipelineResult, setPipelineResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(data => { if (data.app_url) setAppUrl(data.app_url); })
      .catch(() => {});
    // Load last scan if available
    fetch('/api/scan/last')
      .then(r => { if (r.ok) return r.json(); return null; })
      .then(data => { if (data) setScanResult(data); })
      .catch(() => {});
  }, []);

  const handleScan = () => {
    setScanning(true);
    setScanResult(null);
    setError('');
    // Also save the URL to config
    fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_url: appUrl }),
    }).catch(() => {});

    fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: appUrl }),
    })
      .then(r => r.json())
      .then(data => {
        setScanning(false);
        setScanResult(data);
        if (data.errors && data.errors.length > 0 && !data.reachable) {
          setError(data.errors[0]);
        }
      })
      .catch(err => { setScanning(false); setError(String(err)); });
  };

  const handleExecute = () => {
    setRunning(true);
    setPipelineResult(null);
    setError('');
    // Save URL first
    fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ app_url: appUrl }),
    }).catch(() => {});

    fetch('/api/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: appUrl }),
    })
      .then(r => r.json())
      .then(data => {
        setRunning(false);
        if (data.error) {
          setError(data.error);
        } else {
          setPipelineResult(data);
        }
      })
      .catch(err => { setRunning(false); setError(String(err)); });
  };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Execute Pipeline</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Enter any application URL, scan it for screens/fields/APIs, then run the full 10-agent pipeline.
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Target Application</Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField fullWidth size="small" label="Application URL" value={appUrl}
            onChange={e => setAppUrl(e.target.value)} placeholder="https://your-app.com" />
          <Button variant="outlined" startIcon={<Search />} onClick={handleScan} disabled={scanning || running}>
            {scanning ? 'Scanning...' : 'Scan'}
          </Button>
          <Button variant="contained" startIcon={<PlayArrow />} onClick={handleExecute} disabled={scanning || running}>
            {running ? 'Running...' : 'Execute'}
          </Button>
        </Box>
      </Paper>

      {(scanning || running) && <LinearProgress sx={{ mb: 2 }} />}

      {/* Scan Results */}
      {scanResult && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Scan Results — {scanResult.url}
            <Chip label={scanResult.reachable ? 'Reachable' : 'Unreachable'} size="small"
              color={scanResult.reachable ? 'success' : 'error'} sx={{ ml: 1 }} />
            {scanResult.framework_detected !== 'unknown' && (
              <Chip label={scanResult.framework_detected} size="small" color="info" sx={{ ml: 1 }} />
            )}
            <Chip label={`${scanResult.field_count} fields`} size="small" color="primary" sx={{ ml: 1 }} />
          </Typography>

          <Grid container spacing={2} sx={{ mb: 2 }}>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined"><CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h6" color="success.main">{scanResult.screens.filter(s => s.state === 'active').length}</Typography>
                <Typography variant="caption">Active Screens</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined"><CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h6" color="primary">{scanResult.api_endpoints.filter(e => e.available).length}</Typography>
                <Typography variant="caption">API Endpoints</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined"><CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h6" color="secondary">{scanResult.field_count}</Typography>
                <Typography variant="caption">Fields Found</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card variant="outlined"><CardContent sx={{ textAlign: 'center', py: 1 }}>
                <Typography variant="h6">{scanResult.framework_detected}</Typography>
                <Typography variant="caption">Framework</Typography>
              </CardContent></Card>
            </Grid>
          </Grid>

          {scanResult.screens.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>Screens</Typography>
              <Table size="small">
                <TableBody>
                  {scanResult.screens.map(s => (
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

          {scanResult.api_endpoints.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>API Endpoints</Typography>
              <Table size="small">
                <TableBody>
                  {scanResult.api_endpoints.map(ep => (
                    <TableRow key={ep.path}>
                      <TableCell sx={{ width: 80 }}>
                        <Chip label={ep.method} size="small" color={ep.method === 'GET' ? 'success' : 'primary'} />
                      </TableCell>
                      <TableCell><code>{ep.path}</code></TableCell>
                      <TableCell>{ep.description}</TableCell>
                      <TableCell>
                        <Chip label={ep.available ? 'OK' : String(ep.status)} size="small"
                          color={ep.available ? 'success' : 'error'} />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}

          {scanResult.fields.length > 0 && (
            <Box>
              <Typography variant="body2" fontWeight={600} sx={{ mb: 0.5 }}>Fields ({scanResult.field_count})</Typography>
              <Table size="small">
                <TableBody>
                  {scanResult.fields.map((f, i) => (
                    <TableRow key={i}>
                      <TableCell><code>{f.api_name}</code></TableCell>
                      <TableCell>{f.label}</TableCell>
                      <TableCell>{f.type}</TableCell>
                      <TableCell>{f.required && <Chip label="Required" size="small" color="error" />}</TableCell>
                      <TableCell>{f.values_count} values</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Box>
          )}
        </Paper>
      )}

      {/* Pipeline Results */}
      {pipelineResult && (
        <>
          <Alert severity={pipelineResult.status === 'completed' ? 'success' : 'error'} sx={{ mb: 2 }}
            icon={pipelineResult.status === 'completed' ? <CheckCircle /> : <ErrorIcon />}>
            Pipeline {pipelineResult.status} — {pipelineResult.scenarios_passed}/{pipelineResult.scenarios_total} scenarios passed
            {pipelineResult.fields_discovered !== undefined && ` | ${pipelineResult.fields_discovered} fields scanned`}
            {pipelineResult.duration && ` | ${pipelineResult.duration}`}
          </Alert>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="success.main" fontWeight={700}>{pipelineResult.scenarios_passed}/{pipelineResult.scenarios_total}</Typography>
                <Typography variant="caption">Scenarios Passed</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="primary" fontWeight={700}>{pipelineResult.steps || 0}</Typography>
                <Typography variant="caption">Steps</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="success.main" fontWeight={700}>
                  {pipelineResult.scenarios_total > 0 ? Math.round(pipelineResult.scenarios_passed / pipelineResult.scenarios_total * 100) : 0}%
                </Typography>
                <Typography variant="caption">Pass Rate</Typography>
              </CardContent></Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card><CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h5" color="secondary" fontWeight={700}>{pipelineResult.fields_discovered || 0}</Typography>
                <Typography variant="caption">Fields Scanned</Typography>
              </CardContent></Card>
            </Grid>
          </Grid>

          {pipelineResult.agents && (
            <>
              <Typography variant="h6" fontWeight={600} gutterBottom>Agent Pipeline Results</Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow sx={{ bgcolor: 'primary.main' }}>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>#</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Agent</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Decision</TableCell>
                      <TableCell sx={{ color: 'white', fontWeight: 600 }}>Result</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {pipelineResult.agents.map((r, i) => (
                      <TableRow key={r.name}>
                        <TableCell>{i + 1}</TableCell>
                        <TableCell sx={{ fontWeight: 500 }}>{r.name}</TableCell>
                        <TableCell>
                          <Chip label={r.decision} size="small"
                            color={r.decision === 'PROCEED' ? 'success' : r.decision === 'SKIP' ? 'default' : 'error'} />
                        </TableCell>
                        <TableCell>{r.result}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </>
      )}
    </Box>
  );
}
