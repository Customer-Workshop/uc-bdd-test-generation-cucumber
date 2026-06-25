import React from 'react';
import { Box, Typography, Paper, Stepper, Step, StepLabel, StepContent, Chip, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';

const steps = [
  { agent: 'StoryIngestionAgent', desc: 'Fetch user stories from Jira API or load sample test data', inputs: 'Jira URL, Project Key', outputs: 'Stories JSON array', ai: false },
  { agent: 'AnalysisAgent', desc: 'Detect UI framework (Salesforce LWC / React / Angular) and classify complexity', inputs: 'Stories, App URL', outputs: 'Framework type, screen count', ai: true },
  { agent: 'FeatureGenerationAgent', desc: 'Convert stories into Gherkin .feature files with Given/When/Then syntax', inputs: 'Stories, Framework', outputs: '.feature files', ai: true },
  { agent: 'TestDataPreparationAgent', desc: 'Bundle test data per scenario with field values and Selenium config', inputs: 'Feature files, Test data JSON', outputs: 'Data bundles per scenario', ai: false },
  { agent: 'PageObjectAgent', desc: 'Generate POM classes. Uses SelectorsHub to auto-scan for optimal selectors (CSS, XPath, shadow DOM CSS)', inputs: 'Framework, Features, SelectorsHub scan', outputs: 'POM classes with locators', ai: true },
  { agent: 'ExecutionAgent', desc: 'Run Selenium tests via POM page objects against target application', inputs: 'POM, Data bundles, App URL', outputs: 'Test results (pass/fail per scenario)', ai: false },
  { agent: 'ReportingAgent', desc: 'Generate HTML/JUnit/JSON/Copado reports with Chart.js visualizations and Jira traceability', inputs: 'Test results, Jira IDs', outputs: 'HTML report, JUnit XML, JSON', ai: false },
  { agent: 'DeploymentAgent', desc: 'Deploy results to Copado CI/CD: Create Test Run → Upload Results → Attach Reports → Validate → Deploy → Verify', inputs: 'Reports, Copado config', outputs: 'Deployment status', ai: false },
  { agent: 'FeedbackAgent', desc: 'LLM auto-updates .feature files when Git commits change application screens/fields', inputs: 'Git diff, Features', outputs: 'Updated feature files', ai: true },
];

const decisions = [
  { type: 'PROCEED', desc: 'Continue to next step', color: '#2e7d32' },
  { type: 'RETRY', desc: 'Retry current step (max 3)', color: '#ed6c02' },
  { type: 'SKIP', desc: 'Skip step (not configured)', color: '#757575' },
  { type: 'ABORT', desc: 'Stop pipeline on critical failure', color: '#d32f2f' },
  { type: 'DELEGATE', desc: 'Hand off to another agent', color: '#1565c0' },
];

export default function Workflow() {
  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Workflow — 9-Agent Pipeline</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Visual execution flow showing each autonomous agent, its inputs/outputs, and decision logic.
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Stepper orientation="vertical">
          {steps.map((step, idx) => (
            <Step key={step.agent} active>
              <StepLabel>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography fontWeight={600}>Step {idx + 1}: {step.agent}</Typography>
                  {step.ai && <Chip label="AI" size="small" color="secondary" />}
                </Box>
              </StepLabel>
              <StepContent>
                <Typography variant="body2" sx={{ mb: 1 }}>{step.desc}</Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip label={`IN: ${step.inputs}`} size="small" variant="outlined" color="info" />
                  <Chip label={`OUT: ${step.outputs}`} size="small" variant="outlined" color="success" />
                </Box>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Paper>

      <Typography variant="h6" fontWeight={600} gutterBottom>Agent Decision Types</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600 }}>Decision</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {decisions.map(d => (
              <TableRow key={d.type}>
                <TableCell><Chip label={d.type} size="small" sx={{ bgcolor: d.color, color: 'white' }} /></TableCell>
                <TableCell>{d.desc}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
