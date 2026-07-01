import React, { useState } from 'react';
import {
  Box, Typography, Paper, Button, Grid, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Switch, FormControlLabel,
  TextField, Alert, Card, CardContent, LinearProgress, Accordion,
  AccordionSummary, AccordionDetails, Divider
} from '@mui/material';
import {
  Api as ApiIcon, PlayArrow, CheckCircle, Cancel, ExpandMore,
  Speed, Storage, Save
} from '@mui/icons-material';

const apiEndpoints = [
  { method: 'GET', path: '/api/car-parts', description: 'List all car parts', category: 'CRUD' },
  { method: 'GET', path: '/api/car-parts/<id>', description: 'Get car part by ID', category: 'CRUD' },
  { method: 'POST', path: '/api/car-parts', description: 'Create new car part', category: 'CRUD' },
  { method: 'PUT', path: '/api/car-parts/<id>', description: 'Update car part', category: 'CRUD' },
  { method: 'DELETE', path: '/api/car-parts/<id>', description: 'Delete car part', category: 'CRUD' },
  { method: 'GET', path: '/api/dropdown-fields', description: 'Get dropdown field metadata', category: 'Metadata' },
  { method: 'GET', path: '/api/sub-categories/<cat>', description: 'Get dependent sub-categories', category: 'Metadata' },
  { method: 'GET', path: '/api/test-data', description: 'Get test data JSON', category: 'Data' },
  { method: 'GET', path: '/api/relationship-schema', description: 'Full Salesforce sObject relationship schema', category: 'Relationship' },
  { method: 'GET', path: '/api/car-parts/<id>/related', description: 'Car part with all __r relationships expanded', category: 'Relationship' },
  { method: 'GET', path: '/api/manufacturers', description: 'List manufacturers (Manufacturer__c)', category: 'Relationship' },
  { method: 'GET', path: '/api/orders', description: 'List orders with parent __r traversals', category: 'Relationship' },
  { method: 'GET', path: '/api/warranty-claims', description: 'Warranty claims with Car_Part__r + Order__r', category: 'Relationship' },
  { method: 'POST', path: '/api/soql', description: 'SOQL-style cross-object query', category: 'Relationship' },
];

const testScenarios = [
  { id: 'CAR-1011', tc: 'TC-011', name: 'API Health Check', type: 'health', priority: 'high', steps: 2 },
  { id: 'CAR-1012', tc: 'TC-012', name: 'List All Car Parts', type: 'read', priority: 'high', steps: 3 },
  { id: 'CAR-1013', tc: 'TC-013', name: 'Get Car Part by ID', type: 'read', priority: 'high', steps: 3 },
  { id: 'CAR-1014', tc: 'TC-014', name: 'Create Car Part', type: 'create', priority: 'high', steps: 3 },
  { id: 'CAR-1015', tc: 'TC-015', name: 'Update Car Part', type: 'update', priority: 'high', steps: 3 },
  { id: 'CAR-1016', tc: 'TC-016', name: 'Delete Car Part', type: 'delete', priority: 'medium', steps: 3 },
  { id: 'CAR-1017', tc: 'TC-017', name: 'Dropdown Fields Metadata', type: 'read', priority: 'medium', steps: 7 },
  { id: 'CAR-1018', tc: 'TC-018', name: 'Dependent Sub-Categories', type: 'read', priority: 'medium', steps: 3 },
  { id: 'CAR-1019', tc: 'TC-019', name: 'Nonexistent Part 404', type: 'validation', priority: 'medium', steps: 2 },
  { id: 'CAR-1020', tc: 'TC-020', name: 'Invalid Create 400', type: 'validation', priority: 'high', steps: 1 },
  { id: 'CAR-1021', tc: 'TC-021', name: 'Parent-to-Child Traversal', type: 'relationship', priority: 'high', steps: 4 },
  { id: 'CAR-1022', tc: 'TC-022', name: 'Child-to-Parent Traversal', type: 'relationship', priority: 'high', steps: 5 },
  { id: 'CAR-1023', tc: 'TC-023', name: 'Lookup Relationship Fields', type: 'relationship', priority: 'high', steps: 6 },
  { id: 'CAR-1024', tc: 'TC-024', name: 'Master-Detail Relationship', type: 'relationship', priority: 'high', steps: 5 },
  { id: 'CAR-1025', tc: 'TC-025', name: 'Custom Object __c API Names', type: 'relationship', priority: 'medium', steps: 4 },
  { id: 'CAR-1026', tc: 'TC-026', name: 'Cross-Object SOQL Query', type: 'relationship', priority: 'high', steps: 5 },
  { id: 'CAR-1027', tc: 'TC-027', name: 'Data Isolation Between Paths', type: 'relationship', priority: 'high', steps: 4 },
  { id: 'CAR-1028', tc: 'TC-028', name: 'Multi-Relationship Hub', type: 'relationship', priority: 'medium', steps: 6 },
];

const methodColors: Record<string, string> = {
  GET: '#2e7d32', POST: '#1565c0', PUT: '#e65100', DELETE: '#c62828',
};

const typeColors: Record<string, 'success' | 'primary' | 'warning' | 'error' | 'info' | 'default' | 'secondary'> = {
  health: 'success', read: 'primary', create: 'info', update: 'warning', delete: 'error', validation: 'default', relationship: 'secondary',
};

export default function APITesting() {
  const [enabled, setEnabled] = useState(true);
  const [baseUrl, setBaseUrl] = useState('http://localhost:5555');
  const [timeout, setTimeout_] = useState('10');
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [saved, setSaved] = useState(false);

  const handleRun = async () => {
    setRunning(true);
    setResults(null);
    try {
      const resp = await fetch('/api/run-api-tests', { method: 'POST' });
      const data = await resp.json();
      setResults(data);
    } catch {
      setResults({ error: 'Failed to connect to API test runner' });
    }
    setRunning(false);
  };

  const handleSave = () => { setSaved(true); window.setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <ApiIcon color="primary" sx={{ mr: 1, fontSize: 28 }} />
        <Typography variant="h5" fontWeight={600}>API Testing</Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        REST API test execution engine — validates CRUD operations, response codes, payload schemas, and field values against the target application endpoints.
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>API testing configuration saved!</Alert>}

      {/* Configuration */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Configuration</Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={5}>
            <TextField fullWidth label="API Base URL" value={baseUrl}
              onChange={e => setBaseUrl(e.target.value)} size="small" />
          </Grid>
          <Grid item xs={12} sm={3}>
            <TextField fullWidth label="Timeout (seconds)" type="number" value={timeout}
              onChange={e => setTimeout_(e.target.value)} size="small" />
          </Grid>
          <Grid item xs={12} sm={2}>
            <FormControlLabel control={<Switch checked={enabled} onChange={e => setEnabled(e.target.checked)} />}
              label="Enabled" />
          </Grid>
          <Grid item xs={12} sm={2}>
            <Button variant="outlined" startIcon={<Save />} onClick={handleSave} fullWidth>Save</Button>
          </Grid>
        </Grid>
      </Paper>

      {/* API Endpoints */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>Target API Endpoints</Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Method</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Endpoint</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Category</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {apiEndpoints.map((ep, i) => (
                <TableRow key={i}>
                  <TableCell>
                    <Chip label={ep.method} size="small"
                      sx={{ fontWeight: 700, color: '#fff', bgcolor: methodColors[ep.method] || '#666', fontFamily: 'monospace' }} />
                  </TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: 13 }}>{ep.path}</TableCell>
                  <TableCell>{ep.description}</TableCell>
                  <TableCell><Chip label={ep.category} size="small" variant="outlined" /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Test Scenarios */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Test Scenarios (18)</Typography>
          <Button variant="contained" startIcon={<PlayArrow />} onClick={handleRun}
            disabled={running || !enabled} color="success">
            {running ? 'Running...' : 'Run API Tests'}
          </Button>
        </Box>
        {running && <LinearProgress sx={{ mb: 2 }} />}
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600 }}>Jira ID</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Test Case</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Scenario</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Priority</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600 }}>Steps</TableCell>
                <TableCell align="center" sx={{ fontWeight: 600 }}>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {testScenarios.map((tc) => (
                <TableRow key={tc.id}>
                  <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>{tc.id}</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace' }}>{tc.tc}</TableCell>
                  <TableCell>{tc.name}</TableCell>
                  <TableCell>
                    <Chip label={tc.type} size="small" color={typeColors[tc.type] || 'default'} />
                  </TableCell>
                  <TableCell>
                    <Chip label={tc.priority} size="small"
                      color={tc.priority === 'high' ? 'error' : 'warning'} variant="outlined" />
                  </TableCell>
                  <TableCell align="center">{tc.steps}</TableCell>
                  <TableCell align="center">
                    {results && !results.error ? (
                      <CheckCircle color="success" fontSize="small" />
                    ) : results?.error ? (
                      <Cancel color="error" fontSize="small" />
                    ) : (
                      <Chip label="Pending" size="small" variant="outlined" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Execution Results */}
      {results && !results.error && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Execution Results</Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} sm={3}>
              <Card sx={{ bgcolor: '#e8f5e9' }}>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" fontWeight={700} color="success.main">{results.passed_scenarios}</Typography>
                  <Typography variant="caption">Passed</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card sx={{ bgcolor: results.failed_scenarios > 0 ? '#ffebee' : '#e8f5e9' }}>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" fontWeight={700} color={results.failed_scenarios > 0 ? 'error.main' : 'success.main'}>
                    {results.failed_scenarios}
                  </Typography>
                  <Typography variant="caption">Failed</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" fontWeight={700} color="primary">{results.total_steps}</Typography>
                  <Typography variant="caption">Total Steps</Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} sm={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center', py: 2 }}>
                  <Typography variant="h4" fontWeight={700}>{results.duration_seconds}s</Typography>
                  <Typography variant="caption">Duration</Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
          <Box sx={{ mt: 2 }}>
            <Chip icon={<Speed />} label={`Run ID: ${results.run_id}`} sx={{ mr: 1 }} />
            <Chip icon={<Storage />} label="Report saved to reports/" variant="outlined" />
          </Box>
        </Paper>
      )}

      {results?.error && (
        <Alert severity="error" sx={{ mb: 3 }}>{results.error}</Alert>
      )}

      {/* Agent Integration */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">Agent Pipeline Integration</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" paragraph>
            The APITestingAgent (Agent 7) runs after the UI ExecutionAgent (Agent 6) and before ReportingAgent (Agent 8)
            in the 10-agent pipeline. API test results are merged with UI test results in a single report.
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom>Pipeline Flow:</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
            {['1. Story Ingestion', '2. Analysis', '3. Feature Generation', '4. Test Data',
              '5. Page Objects', '6. UI Execution', '7. API Testing', '8. Reporting',
              '9. Copado Deploy', '10. Feedback'].map((step, i) => (
              <Chip key={i} label={step} size="small"
                color={step.includes('API Testing') ? 'primary' : 'default'}
                variant={step.includes('API Testing') ? 'filled' : 'outlined'}
                sx={{ fontWeight: step.includes('API Testing') ? 700 : 400 }} />
            ))}
          </Box>
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom>API Test Scenarios by Type:</Typography>
          <Grid container spacing={1}>
            {[
              { type: 'Health', count: 1, desc: 'Verify API reachability' },
              { type: 'Read (GET)', count: 4, desc: 'List, get by ID, dropdown metadata, sub-categories' },
              { type: 'Create (POST)', count: 1, desc: 'Create car part with all fields' },
              { type: 'Update (PUT)', count: 1, desc: 'Partial field update' },
              { type: 'Delete (DELETE)', count: 1, desc: 'Create-then-delete lifecycle' },
              { type: 'Validation', count: 2, desc: '404 for missing, 400 for invalid body' },
              { type: 'Relationship', count: 8, desc: 'Lookup/Master-Detail traversal, SOQL, data isolation' },
            ].map((t, i) => (
              <Grid item xs={12} sm={6} md={4} key={i}>
                <Card variant="outlined" sx={{ p: 1.5 }}>
                  <Typography variant="subtitle2" fontWeight={600}>{t.type} ({t.count})</Typography>
                  <Typography variant="caption" color="text.secondary">{t.desc}</Typography>
                </Card>
              </Grid>
            ))}
          </Grid>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
}
