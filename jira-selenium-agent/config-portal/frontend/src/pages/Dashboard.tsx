import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Typography, Card, CardContent, Grid, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button } from '@mui/material';
import { PlayArrow, Settings, Assessment, BugReport } from '@mui/icons-material';

const statusItems = [
  { tool: 'Application URL', status: 'Configured', color: 'success' as const, path: '/app-configure' },
  { tool: 'Test Data', status: 'Loaded (6 records)', color: 'success' as const, path: '/upload-test-data' },
  { tool: 'Jira', status: 'Not Configured', color: 'default' as const, path: '/jira-config' },
  { tool: 'Selenium', status: 'Configured', color: 'success' as const, path: '/selenium-config' },
  { tool: 'GitHub', status: 'Not Configured', color: 'default' as const, path: '/github-config' },
  { tool: 'Copado', status: 'Disabled', color: 'warning' as const, path: '/copado-config' },
  { tool: 'AI Model', status: 'GPT-4o', color: 'info' as const, path: '/ai-model' },
  { tool: 'Reports', status: 'HTML + Charts', color: 'success' as const, path: '/report-config' },
  { tool: 'SelectorsHub', status: 'Enabled', color: 'success' as const, path: '/selectorshub-config' },
  { tool: 'MCP Servers', status: 'Disabled', color: 'warning' as const, path: '/mcp-servers' },
  { tool: 'API Testing', status: 'Enabled (18 scenarios)', color: 'success' as const, path: '/api-testing' },
  { tool: 'Relationships', status: '6 objects, 8 tests', color: 'success' as const, path: '/relationships' },
];

const stats = [
  { label: 'UI + API Tests', value: '24', color: '#1565c0' },
  { label: 'Total Steps', value: '127', color: '#2e7d32' },
  { label: 'Pass Rate', value: '100%', color: '#ed6c02' },
  { label: 'Agents', value: '10', color: '#7b1fa2' },
];

export default function Dashboard() {
  const navigate = useNavigate();
  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Dashboard</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Automation Configuration Portal — manage all settings for the 10-agent BDD test pipeline (UI + API testing).
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {stats.map(s => (
          <Grid item xs={6} sm={3} key={s.label}>
            <Card sx={{ borderTop: `3px solid ${s.color}` }}>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" fontWeight={700} sx={{ color: s.color }}>{s.value}</Typography>
                <Typography variant="caption" color="text.secondary">{s.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={3}>
          <Button fullWidth variant="contained" startIcon={<PlayArrow />} onClick={() => navigate('/execute')}>Execute Pipeline</Button>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Button fullWidth variant="outlined" startIcon={<Assessment />} onClick={() => navigate('/report-config')}>View Reports</Button>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Button fullWidth variant="outlined" startIcon={<Settings />} onClick={() => navigate('/workflow')}>Workflow</Button>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Button fullWidth variant="outlined" startIcon={<BugReport />} onClick={() => navigate('/traceability')}>Traceability</Button>
        </Grid>
      </Grid>

      <Typography variant="h6" fontWeight={600} gutterBottom>Integration Status</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Tool</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Status</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {statusItems.map(item => (
              <TableRow key={item.tool} hover>
                <TableCell sx={{ fontWeight: 500 }}>{item.tool}</TableCell>
                <TableCell><Chip label={item.status} size="small" color={item.color} /></TableCell>
                <TableCell>
                  <Button size="small" onClick={() => navigate(item.path)}>Configure</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
