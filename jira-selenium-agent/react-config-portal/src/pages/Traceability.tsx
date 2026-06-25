import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, Chip, Accordion, AccordionSummary, AccordionDetails, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from '@mui/material';
import { ExpandMore } from '@mui/icons-material';

const traceData = [
  { jira: 'CAR-1001', tc: 'TC-001', name: 'Create Engine Component (Turbocharger)', priority: 'High', steps: 11, dataFields: 17,
    story: 'As a warehouse manager, I want to create a new engine component record with all required fields.',
    execSteps: ['Navigate to Car Parts', 'Click New Car Part', 'Fill Part Name', 'Fill Part Number', 'Select Part Category', 'Select Sub-Category', 'Select Manufacturer', 'Select Condition', 'Fill Price', 'Fill Stock', 'Click Save'],
    fields: { part_name: 'Turbocharger Assembly', part_number: 'TB-ENG-2024-001', part_category: 'Engine Components', part_sub_category: 'Turbocharger', manufacturer: 'BorgWarner', condition: 'New' }
  },
  { jira: 'CAR-1002', tc: 'TC-002', name: 'Create Braking System Part (Brake Kit)', priority: 'High', steps: 10, dataFields: 15,
    story: 'As a warehouse manager, I want to create a braking system part with dependent picklist selection.',
    execSteps: ['Navigate to Car Parts', 'Click New', 'Fill Basic Info', 'Select Braking System', 'Select Brake Kit', 'Select Brembo', 'Fill Pricing', 'Fill Logistics', 'Verify form', 'Save'],
    fields: { part_name: 'Performance Brake Kit', part_category: 'Braking System', part_sub_category: 'Brake Kit', manufacturer: 'Brembo' }
  },
  { jira: 'CAR-1003', tc: 'TC-003', name: 'Create Suspension Part (Coilover)', priority: 'Medium', steps: 10, dataFields: 15,
    story: 'As a parts manager, I want to add suspension components to inventory.',
    execSteps: ['Navigate to List', 'Click New', 'Fill Part Name/Number', 'Select Suspension & Steering', 'Select Coilover Kit', 'Select KYB', 'Set Low Stock', 'Fill pricing', 'Verify', 'Save'],
    fields: { part_name: 'Coilover Suspension Kit', part_category: 'Suspension & Steering', manufacturer: 'KYB', availability: 'Low Stock' }
  },
  { jira: 'CAR-1004', tc: 'TC-004', name: 'Create Electrical Part (LED Headlight)', priority: 'Medium', steps: 11, dataFields: 15,
    story: 'As a parts manager, I want to add electrical lighting components.',
    execSteps: ['Navigate', 'New Part', 'Part Name', 'Part Number', 'Category: Electrical', 'Sub: LED Headlight', 'Manufacturer: Hella', 'Vehicle: Tesla', 'Year: 2024-2025', 'Pricing', 'Save'],
    fields: { part_name: 'LED Headlight Assembly', part_category: 'Electrical & Lighting', manufacturer: 'Hella', vehicle_make: 'Tesla' }
  },
  { jira: 'CAR-1005', tc: 'TC-005', name: 'Edit Existing Car Part', priority: 'High', steps: 10, dataFields: 2,
    story: 'As a manager, I want to edit an existing car part to update its condition and availability.',
    execSteps: ['Navigate to List', 'Find record', 'Click Edit', 'Change Condition to Refurbished', 'Change Availability to Low Stock', 'Save', 'Verify changes', 'Check toast', 'Verify list update', 'Confirm'],
    fields: { condition: 'Refurbished', availability: 'Low Stock' }
  },
  { jira: 'CAR-1006', tc: 'TC-006', name: 'Delete Car Part', priority: 'Medium', steps: 6, dataFields: 1,
    story: 'As a manager, I want to delete a car part record from the system.',
    execSteps: ['Navigate to List', 'Find target record', 'Click Delete', 'Confirm dialog', 'Verify removed', 'Check toast'],
    fields: { target: 'LED Headlight Assembly' }
  },
];

export default function Traceability() {
  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom>Traceability Matrix</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Jira Story → Test Case → Execution Steps → Test Data mapping for full end-to-end traceability.
      </Typography>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card sx={{ borderTop: '3px solid #1565c0' }}><CardContent sx={{ textAlign: 'center', py: 1.5 }}>
            <Typography variant="h5" fontWeight={700} color="primary">6</Typography>
            <Typography variant="caption">Jira Stories</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card sx={{ borderTop: '3px solid #2e7d32' }}><CardContent sx={{ textAlign: 'center', py: 1.5 }}>
            <Typography variant="h5" fontWeight={700} color="success.main">6</Typography>
            <Typography variant="caption">Test Cases</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card sx={{ borderTop: '3px solid #ed6c02' }}><CardContent sx={{ textAlign: 'center', py: 1.5 }}>
            <Typography variant="h5" fontWeight={700} color="warning.main">58</Typography>
            <Typography variant="caption">Execution Steps</Typography>
          </CardContent></Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card sx={{ borderTop: '3px solid #7b1fa2' }}><CardContent sx={{ textAlign: 'center', py: 1.5 }}>
            <Typography variant="h5" fontWeight={700} color="secondary">65</Typography>
            <Typography variant="caption">Data Fields</Typography>
          </CardContent></Card>
        </Grid>
      </Grid>

      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Jira Story</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Test Case</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Scenario</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Priority</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Steps</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Data Fields</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {traceData.map(t => (
              <TableRow key={t.jira} hover>
                <TableCell><Chip label={t.jira} size="small" color="info" /></TableCell>
                <TableCell><Chip label={t.tc} size="small" variant="outlined" /></TableCell>
                <TableCell>{t.name}</TableCell>
                <TableCell><Chip label={t.priority} size="small" color={t.priority === 'High' ? 'error' : 'warning'} /></TableCell>
                <TableCell>{t.steps}</TableCell>
                <TableCell>{t.dataFields}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography variant="h6" fontWeight={600} gutterBottom>Detailed Traceability</Typography>
      {traceData.map(t => (
        <Accordion key={t.jira}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip label={t.jira} size="small" color="info" />
              <Chip label={t.tc} size="small" variant="outlined" />
              <Typography fontWeight={500}>{t.name}</Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" sx={{ mb: 1, fontStyle: 'italic' }}>{t.story}</Typography>
            <Typography variant="subtitle2" fontWeight={600} sx={{ mt: 1 }}>Execution Steps:</Typography>
            <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mb: 1 }}>
              {t.execSteps.map((step, i) => (
                <Chip key={i} label={`${i + 1}. ${step}`} size="small" variant="outlined" />
              ))}
            </Box>
            <Typography variant="subtitle2" fontWeight={600}>Test Data:</Typography>
            <Table size="small">
              <TableBody>
                {Object.entries(t.fields).map(([k, v]) => (
                  <TableRow key={k}>
                    <TableCell sx={{ fontFamily: 'monospace', color: 'primary.main' }}>{k}</TableCell>
                    <TableCell>{v}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
