import React from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Card, CardContent, Grid, Accordion,
  AccordionSummary, AccordionDetails
} from '@mui/material';
import { ExpandMore as ExpandIcon, DataObject as DataIcon } from '@mui/icons-material';

const testScenarios = [
  {
    jira_id: 'CAR-1001',
    test_case: 'TC-001',
    name: 'Create Engine Component (Turbocharger)',
    priority: 'High',
    fields: {
      part_name: 'Turbocharger Assembly',
      part_number: 'TB-ENG-2024-001',
      part_category: 'Engine Components',
      part_sub_category: 'Turbocharger',
      manufacturer: 'BorgWarner',
      condition: 'New',
      vehicle_make: 'BMW',
      year_range: '2022-2023',
      unit_price: '1250.00',
      stock_quantity: '15',
      availability: 'In Stock',
      warehouse_location: 'Main Warehouse - A1',
      quality_grade: 'OEM',
      shipping_class: 'Freight',
      warranty_type: 'Manufacturer Warranty',
      currency: 'USD',
      description: 'High-performance turbocharger for BMW 3-series'
    }
  },
  {
    jira_id: 'CAR-1002',
    test_case: 'TC-002',
    name: 'Create Braking System (Brake Kit)',
    priority: 'High',
    fields: {
      part_name: 'Performance Brake Kit',
      part_number: 'BK-BRK-2024-002',
      part_category: 'Braking System',
      part_sub_category: 'Brake Kit',
      manufacturer: 'Brembo',
      condition: 'New',
      vehicle_make: 'Mercedes-Benz',
      year_range: '2020-2021',
      unit_price: '890.00',
      stock_quantity: '22',
      availability: 'In Stock',
      warehouse_location: 'Main Warehouse - B2',
      quality_grade: 'Premium Aftermarket',
      shipping_class: 'Oversized',
      warranty_type: '2-Year Warranty',
      currency: 'USD'
    }
  },
  {
    jira_id: 'CAR-1003',
    test_case: 'TC-003',
    name: 'Create Suspension Part (Coilover)',
    priority: 'Medium',
    fields: {
      part_name: 'Coilover Suspension Kit',
      part_number: 'SK-SUS-2024-003',
      part_category: 'Suspension & Steering',
      part_sub_category: 'Coilover Kit',
      manufacturer: 'KYB',
      condition: 'New',
      vehicle_make: 'Honda',
      year_range: '2020-2021',
      unit_price: '675.00',
      stock_quantity: '8',
      availability: 'Low Stock',
      warehouse_location: 'Secondary Warehouse - D1',
      quality_grade: 'OEM Equivalent',
      shipping_class: 'Standard',
      warranty_type: '1-Year Warranty',
      currency: 'USD'
    }
  },
  {
    jira_id: 'CAR-1004',
    test_case: 'TC-004',
    name: 'Create Electrical Part (LED Headlight)',
    priority: 'Medium',
    fields: {
      part_name: 'LED Headlight Assembly',
      part_number: 'HL-ELC-2024-004',
      part_category: 'Electrical & Lighting',
      part_sub_category: 'LED Headlight',
      manufacturer: 'Hella',
      condition: 'New',
      vehicle_make: 'Tesla',
      year_range: '2024-2025',
      unit_price: '450.00',
      stock_quantity: '30',
      availability: 'In Stock',
      warehouse_location: 'Main Warehouse - C3',
      quality_grade: 'OEM',
      shipping_class: 'Standard',
      warranty_type: 'Manufacturer Warranty',
      currency: 'USD'
    }
  },
  {
    jira_id: 'CAR-1005',
    test_case: 'TC-005',
    name: 'Edit Existing Car Part',
    priority: 'High',
    fields: {
      condition: 'Refurbished',
      availability: 'Low Stock'
    }
  },
  {
    jira_id: 'CAR-1006',
    test_case: 'TC-006',
    name: 'Delete Car Part',
    priority: 'Medium',
    fields: {
      target: 'LED Headlight Assembly'
    }
  }
];

export default function TestData() {
  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom data-testid="test-data-title">
        Test Data — Selenium Execution Reference
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Data used by Selenium BDD test scenarios during E2E execution. Each scenario maps to a Jira story and uses these field values.
      </Typography>

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[
          { label: 'Scenarios', value: '6', color: '#1976d2' },
          { label: 'Dropdown Fields', value: '12', color: '#2e7d32' },
          { label: 'Picklist Values', value: '153', color: '#ed6c02' },
          { label: 'Dependent Categories', value: '5', color: '#9c27b0' },
        ].map(stat => (
          <Grid item xs={6} sm={3} key={stat.label}>
            <Card sx={{ borderTop: `3px solid ${stat.color}` }}>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h4" sx={{ fontWeight: 700, color: stat.color }}>{stat.value}</Typography>
                <Typography variant="caption" color="text.secondary">{stat.label}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Test Scenarios */}
      {testScenarios.map((scenario) => (
        <Accordion key={scenario.jira_id} defaultExpanded={scenario.jira_id === 'CAR-1001'}>
          <AccordionSummary expandIcon={<ExpandIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
              <Chip label={scenario.jira_id} size="small" color="primary" />
              <Chip label={scenario.test_case} size="small" variant="outlined" />
              <Typography sx={{ fontWeight: 500, flexGrow: 1 }}>{scenario.name}</Typography>
              <Chip
                label={scenario.priority}
                size="small"
                color={scenario.priority === 'High' ? 'error' : 'warning'}
              />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 600 }}>Field</TableCell>
                    <TableCell sx={{ fontWeight: 600 }}>Value</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {Object.entries(scenario.fields).map(([field, value]) => (
                    <TableRow key={field}>
                      <TableCell sx={{ fontFamily: 'monospace', color: 'primary.main' }}>
                        {field}
                      </TableCell>
                      <TableCell>{value}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </AccordionDetails>
        </Accordion>
      ))}

      {/* Raw JSON */}
      <Paper sx={{ p: 2, mt: 3, bgcolor: '#1e1e1e' }}>
        <Typography variant="subtitle2" color="grey.400" gutterBottom>
          <DataIcon sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
          Raw Test Data JSON Source
        </Typography>
        <Box component="pre" sx={{ color: '#d4d4d4', fontSize: 12, overflow: 'auto', maxHeight: 300 }}>
          {JSON.stringify(testScenarios, null, 2)}
        </Box>
      </Paper>
    </Box>
  );
}
