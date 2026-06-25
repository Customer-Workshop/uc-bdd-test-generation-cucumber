import React, { useState } from 'react';
import { Box, Typography, Paper, Grid, Switch, FormControlLabel, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Accordion, AccordionSummary, AccordionDetails, Select, MenuItem, FormControl, InputLabel, Button, Alert } from '@mui/material';
import { ExpandMore, Save } from '@mui/icons-material';

const servers = [
  { name: 'Jira MCP', port: 3001, tools: ['search_stories', 'get_story', 'update_status', 'create_story', 'get_project_config'], desc: 'Jira story management' },
  { name: 'Selenium MCP', port: 3002, tools: ['run_scenario', 'click_element', 'fill_form', 'screenshot', 'get_page_source', 'wait_for_element'], desc: 'Browser automation' },
  { name: 'Copado MCP', port: 3003, tools: ['create_test_run', 'upload_results', 'trigger_deployment', 'get_pipeline_status', 'promote_environment'], desc: 'CI/CD deployment' },
  { name: 'GitHub MCP', port: 3004, tools: ['list_commits', 'get_diff', 'create_pr', 'trigger_workflow', 'get_file_content'], desc: 'Repository operations' },
  { name: 'SelectorsHub MCP', port: 3005, tools: ['scan_page', 'get_selectors', 'generate_pom', 'scan_shadow_dom', 'validate_selector'], desc: 'Element scanning' },
];

export default function MCPServers() {
  const [globalEnabled, setGlobalEnabled] = useState(false);
  const [transport, setTransport] = useState('stdio');
  const [saved, setSaved] = useState(false);

  const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 3000); };

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>MCP Servers</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Model Context Protocol servers exposing tools via JSON-RPC for any LLM host (Claude Desktop, GPT, Cursor).
      </Typography>

      {saved && <Alert severity="success" sx={{ mb: 2 }}>MCP configuration saved!</Alert>}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <FormControlLabel control={<Switch checked={globalEnabled} onChange={e => setGlobalEnabled(e.target.checked)} />}
              label="Enable MCP Servers" />
          </Grid>
          <Grid item xs={12} sm={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Transport</InputLabel>
              <Select value={transport} label="Transport" onChange={e => setTransport(e.target.value)}>
                <MenuItem value="stdio">stdio</MenuItem>
                <MenuItem value="sse">SSE (Server-Sent Events)</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Button variant="contained" startIcon={<Save />} onClick={handleSave}>Save</Button>
          </Grid>
        </Grid>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>Available Servers</Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Server</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Port</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Description</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Tools</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {servers.map(s => (
              <TableRow key={s.name} hover>
                <TableCell sx={{ fontWeight: 500 }}>{s.name}</TableCell>
                <TableCell><code>{s.port}</code></TableCell>
                <TableCell>{s.desc}</TableCell>
                <TableCell>{s.tools.length} tools</TableCell>
                <TableCell><Chip label={globalEnabled ? 'Ready' : 'Disabled'} size="small" color={globalEnabled ? 'success' : 'default'} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6" fontWeight={600} gutterBottom>Tool Definitions</Typography>
      {servers.map(s => (
        <Accordion key={s.name}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography fontWeight={500}>{s.name}</Typography>
              <Chip label={`Port ${s.port}`} size="small" variant="outlined" />
              <Chip label={`${s.tools.length} tools`} size="small" color="primary" />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
              {s.tools.map(t => (
                <Chip key={t} label={t} size="small" variant="outlined" sx={{ fontFamily: 'monospace', fontSize: 11 }} />
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}

      <Paper sx={{ p: 2, mt: 3, bgcolor: 'grey.900' }}>
        <Typography variant="subtitle2" sx={{ color: 'grey.300', mb: 1 }}>mcp.json (Claude Desktop)</Typography>
        <pre style={{ color: '#4fc3f7', fontSize: 11, margin: 0, overflow: 'auto' }}>{`{
  "mcpServers": {
    "jira": { "command": "python", "args": ["mcp_jira_server.py"], "port": 3001 },
    "selenium": { "command": "python", "args": ["mcp_selenium_server.py"], "port": 3002 },
    "copado": { "command": "python", "args": ["mcp_copado_server.py"], "port": 3003 },
    "github": { "command": "python", "args": ["mcp_github_server.py"], "port": 3004 },
    "selectorshub": { "command": "python", "args": ["mcp_selectorshub_server.py"], "port": 3005 }
  }
}`}</pre>
      </Paper>
    </Box>
  );
}
