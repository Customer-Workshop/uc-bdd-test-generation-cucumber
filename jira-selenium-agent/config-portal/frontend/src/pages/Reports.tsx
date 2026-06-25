import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Divider } from '@mui/material';

const kpis = [
  { label: 'Total Scenarios', value: '10', color: '#1565c0' },
  { label: 'Passed', value: '10', color: '#2e7d32' },
  { label: 'Failed', value: '0', color: '#d32f2f' },
  { label: 'Skipped', value: '0', color: '#ed6c02' },
  { label: 'Pass Rate', value: '100.0%', color: '#7b1fa2' },
  { label: 'Total Steps', value: '238', color: '#0097a7' },
];

const scenarios = [
  { jira: 'CAR-1001', name: 'Create Engine Component (Turbocharger)', steps: 29, duration: '4.2s', status: 'PASSED' },
  { jira: 'CAR-1002', name: 'Create Braking System (Brake Kit)', steps: 23, duration: '3.8s', status: 'PASSED' },
  { jira: 'CAR-1003', name: 'Create Suspension (Coilover Kit)', steps: 19, duration: '3.1s', status: 'PASSED' },
  { jira: 'CAR-1004', name: 'Create Electrical (LED Headlight)', steps: 19, duration: '3.0s', status: 'PASSED' },
  { jira: 'CAR-1005', name: 'Traverse All Dropdown Fields', steps: 80, duration: '8.5s', status: 'PASSED' },
  { jira: 'CAR-1006', name: 'Edit Existing Car Part', steps: 14, duration: '2.4s', status: 'PASSED' },
  { jira: 'CAR-1007', name: 'Search and Filter', steps: 11, duration: '1.9s', status: 'PASSED' },
  { jira: 'CAR-1008', name: 'Verify Dependent Picklists', steps: 27, duration: '4.0s', status: 'PASSED' },
  { jira: 'CAR-1009', name: 'Delete Car Part', steps: 7, duration: '1.2s', status: 'PASSED' },
  { jira: 'CAR-1010', name: 'Validate Required Fields', steps: 9, duration: '1.5s', status: 'PASSED' },
];

export default function Reports() {
  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Test Execution Report</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Chip label="HTML" size="small" color="primary" />
        <Chip label="Chart.js" size="small" color="secondary" />
        <Chip label="Auto-updates from Execute" size="small" variant="outlined" />
        <Typography variant="caption" color="text.secondary">Last run: Pipeline Execution</Typography>
      </Box>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {kpis.map(k => (
          <Grid item xs={6} sm={2} key={k.label}>
            <Card sx={{ borderTop: `3px solid ${k.color}` }}>
              <CardContent sx={{ textAlign: 'center', py: 1.5 }}>
                <Typography variant="h5" fontWeight={700} sx={{ color: k.color }}>{k.value}</Typography>
                <Typography variant="caption" color="text.secondary">{k.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" fontWeight={600} gutterBottom>Scenario Results with Jira IDs</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Jira ID</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Scenario</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Steps</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Duration</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {scenarios.map(s => (
              <TableRow key={s.jira} hover>
                <TableCell><Chip label={s.jira} size="small" color="info" variant="outlined" /></TableCell>
                <TableCell>{s.name}</TableCell>
                <TableCell>{s.steps}</TableCell>
                <TableCell>{s.duration}</TableCell>
                <TableCell><Chip label={s.status} size="small" color="success" /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="subtitle2" fontWeight={600} gutterBottom>Copado Report Deployment</Typography>
        <Table size="small">
          <TableBody>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell><Chip label="Not Configured" size="small" color="default" /></TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Report Formats</TableCell>
              <TableCell>HTML (Chart.js) + JUnit XML + JSON</TableCell>
            </TableRow>
            <TableRow>
              <TableCell>Copado Attachment</TableCell>
              <TableCell>Reports auto-attached to copado__Test_Run__c when enabled</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </Paper>
    </Box>
  );
}
