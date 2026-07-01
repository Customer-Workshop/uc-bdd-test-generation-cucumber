import React from 'react';
import { Box, Typography, Paper, Grid, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Divider } from '@mui/material';

const agentFlow = [
  { agent: 'StoryIngestionAgent', receives: 'Jira API / JSON', produces: 'Stories[]', sends: 'AnalysisAgent', external: 'Jira' },
  { agent: 'AnalysisAgent', receives: 'Stories[]', produces: 'Framework + Screens', sends: 'FeatureGenerationAgent', external: 'Target App' },
  { agent: 'FeatureGenerationAgent', receives: 'Stories + Framework', produces: '.feature files', sends: 'TestDataPrepAgent', external: 'LLM' },
  { agent: 'TestDataPreparationAgent', receives: '.feature + Test Data', produces: 'Data Bundles[]', sends: 'PageObjectAgent', external: '-' },
  { agent: 'PageObjectAgent', receives: 'Framework + Features', produces: 'POM Classes', sends: 'ExecutionAgent', external: 'SelectorsHub' },
  { agent: 'ExecutionAgent', receives: 'POM + Data + URL', produces: 'UI Results[]', sends: 'APITestingAgent', external: 'Selenium' },
  { agent: 'APITestingAgent', receives: 'App URL + Test Data + Relationship Schema', produces: 'API Results[] (10 CRUD + 8 Relationship)', sends: 'ReportingAgent', external: 'REST API + SOQL' },
  { agent: 'ReportingAgent', receives: 'UI + API Results', produces: 'HTML/XML/JSON', sends: 'DeploymentAgent', external: '-' },
  { agent: 'DeploymentAgent', receives: 'Reports + Config', produces: 'Deploy Status', sends: 'FeedbackAgent', external: 'Copado' },
  { agent: 'FeedbackAgent', receives: 'Git Diff + Features', produces: 'Updated Features', sends: 'Orchestrator', external: 'GitHub' },
];

const externalSystems = [
  { name: 'Jira', purpose: 'User story source', protocol: 'REST API' },
  { name: 'GitHub', purpose: 'Code repository & CI', protocol: 'REST API / Webhooks' },
  { name: 'Salesforce UI', purpose: 'Target application', protocol: 'HTTP (Selenium)' },
  { name: 'LLM Provider', purpose: 'AI test generation', protocol: 'API (OpenAI/Claude)' },
  { name: 'Copado', purpose: 'CI/CD deployment', protocol: 'REST API' },
  { name: 'Selenium', purpose: 'Browser automation', protocol: 'WebDriver / CDP' },
  { name: 'SelectorsHub', purpose: 'Element scanning', protocol: 'CDP Extension' },
];

export default function FlowDiagram() {
  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Architecture Flow Diagram</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Complete system architecture showing agent communication, external integrations, and data flow.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>MCP Server Status</Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Aspect</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>This Framework</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>MCP Standard</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow><TableCell>Orchestration</TableCell><TableCell>AgenticOrchestrator (in-memory)</TableCell><TableCell>LLM Host (Claude/GPT)</TableCell></TableRow>
            <TableRow><TableCell>Communication</TableCell><TableCell>Dict passing between agents</TableCell><TableCell>JSON-RPC over stdio/SSE</TableCell></TableRow>
            <TableRow><TableCell>LLM Integration</TableCell><TableCell>Optional (FeatureGen, Feedback)</TableCell><TableCell>Required (LLM is orchestrator)</TableCell></TableRow>
            <TableRow><TableCell>External Tools</TableCell><TableCell>Direct API calls from agents</TableCell><TableCell>Tool definitions via MCP protocol</TableCell></TableRow>
            <TableRow><TableCell>State</TableCell><TableCell>In-memory context dict</TableCell><TableCell>Stateless (per-request)</TableCell></TableRow>
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>10-Agent Pipeline Flow</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {agentFlow.map((a, i) => (
            <React.Fragment key={a.agent}>
              <Chip label={`${i + 1}. ${a.agent.replace('Agent', '')}`} color="primary" size="small" />
              {i < agentFlow.length - 1 && <Typography color="text.secondary" variant="body2">→</Typography>}
            </React.Fragment>
          ))}
        </Box>
        <Typography variant="caption" color="text.secondary">
          Each agent follows: decide() → act() → report() lifecycle. Decisions: PROCEED | RETRY | SKIP | ABORT | DELEGATE
        </Typography>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>Agent Communication Sequence</Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>#</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Agent</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Receives From</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Produces</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Sends To</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>External</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {agentFlow.map((a, i) => (
              <TableRow key={a.agent} hover>
                <TableCell>{i + 1}</TableCell>
                <TableCell sx={{ fontWeight: 500, fontSize: 12 }}>{a.agent}</TableCell>
                <TableCell><Typography variant="caption">{a.receives}</Typography></TableCell>
                <TableCell><Typography variant="caption">{a.produces}</Typography></TableCell>
                <TableCell><Typography variant="caption">{a.sends}</Typography></TableCell>
                <TableCell>{a.external !== '-' ? <Chip label={a.external} size="small" variant="outlined" /> : '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Divider sx={{ my: 2 }} />
      <Typography variant="h6" fontWeight={600} gutterBottom>External Systems</Typography>
      <Grid container spacing={2}>
        {externalSystems.map(sys => (
          <Grid item xs={12} sm={6} md={4} key={sys.name}>
            <Paper sx={{ p: 2, height: '100%' }}>
              <Typography fontWeight={600}>{sys.name}</Typography>
              <Typography variant="body2" color="text.secondary">{sys.purpose}</Typography>
              <Chip label={sys.protocol} size="small" sx={{ mt: 1 }} />
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Copado CI/CD Pipeline</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {['Create Test Run', 'Upload Results', 'Attach Reports', 'Validate Pipeline', 'Trigger Deployment', 'Verify Promotion'].map((stage, i) => (
            <React.Fragment key={stage}>
              <Chip label={`${i + 1}. ${stage}`} color="secondary" size="small" variant="outlined" />
              {i < 5 && <Typography color="text.secondary">→</Typography>}
            </React.Fragment>
          ))}
        </Box>
        <Typography variant="subtitle2" fontWeight={600}>Environment Promotion Path:</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
          {['DEV', 'SIT', 'UAT', 'STAGING', 'PRODUCTION'].map((env, i) => (
            <React.Fragment key={env}>
              <Chip label={env} size="small" color={i < 3 ? 'success' : 'default'} />
              {i < 4 && <Typography color="text.secondary">→</Typography>}
            </React.Fragment>
          ))}
        </Box>
      </Paper>
    </Box>
  );
}
