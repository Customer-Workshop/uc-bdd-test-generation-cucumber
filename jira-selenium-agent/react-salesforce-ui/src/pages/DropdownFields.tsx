import React from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Chip, Grid, Card, CardContent, Accordion,
  AccordionSummary, AccordionDetails
} from '@mui/material';
import { ExpandMore as ExpandIcon } from '@mui/icons-material';
import { dropdownFields, subCategoryMap } from '../data/carPartsData';

export default function DropdownFields() {
  const fieldMeta = [
    { name: 'part_category', label: 'Part Category', api: 'Part_Category__c', required: true, dependent: false },
    { name: 'part_sub_category', label: 'Part Sub-Category', api: 'Part_Sub_Category__c', required: false, dependent: true },
    { name: 'manufacturer', label: 'Manufacturer', api: 'Manufacturer__c', required: true, dependent: false },
    { name: 'condition', label: 'Condition', api: 'Condition__c', required: true, dependent: false },
    { name: 'vehicle_make', label: 'Vehicle Make', api: 'Vehicle_Make__c', required: false, dependent: false },
    { name: 'year_range', label: 'Year Range', api: 'Year_Range__c', required: false, dependent: false },
    { name: 'availability', label: 'Availability', api: 'Availability__c', required: false, dependent: false },
    { name: 'warehouse_location', label: 'Warehouse Location', api: 'Warehouse_Location__c', required: false, dependent: false },
    { name: 'quality_grade', label: 'Quality Grade', api: 'Quality_Grade__c', required: false, dependent: false },
    { name: 'shipping_class', label: 'Shipping Class', api: 'Shipping_Class__c', required: false, dependent: false },
    { name: 'warranty_type', label: 'Warranty Type', api: 'Warranty_Type__c', required: false, dependent: false },
    { name: 'currency', label: 'Currency', api: 'Currency__c', required: false, dependent: false },
  ];

  const totalValues = Object.values(dropdownFields).reduce((sum, arr) => sum + arr.length, 0) +
    Object.values(subCategoryMap).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <Box>
      <Typography variant="h5" fontWeight={600} gutterBottom data-testid="dropdown-fields-title">
        Dropdown Fields Reference
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        All 12 picklist/dropdown fields with their values. Part Sub-Category is a dependent field controlled by Part Category.
      </Typography>

      {/* Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[
          { label: 'Dropdown Fields', value: '12', color: '#1976d2' },
          { label: 'Total Values', value: String(totalValues), color: '#2e7d32' },
          { label: 'Dependent Fields', value: '1', color: '#ed6c02' },
          { label: 'Category Groups', value: String(Object.keys(subCategoryMap).length), color: '#9c27b0' },
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

      {/* Field API Names Table */}
      <Paper sx={{ mb: 3 }}>
        <TableContainer>
          <Table size="small" data-testid="fields-table">
            <TableHead>
              <TableRow sx={{ bgcolor: 'primary.main' }}>
                <TableCell sx={{ color: 'white', fontWeight: 600 }}>#</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 600 }}>Field Label</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 600 }}>API Name</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 600 }}>Values</TableCell>
                <TableCell sx={{ color: 'white', fontWeight: 600 }}>Badges</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {fieldMeta.map((field, idx) => (
                <TableRow key={field.name} hover>
                  <TableCell>{idx + 1}</TableCell>
                  <TableCell sx={{ fontWeight: 500 }}>{field.label}</TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', fontSize: 12 }}>{field.api}</TableCell>
                  <TableCell>
                    {field.name === 'part_sub_category'
                      ? `${Object.values(subCategoryMap).reduce((s, a) => s + a.length, 0)} (dependent)`
                      : dropdownFields[field.name]?.length || 0}
                  </TableCell>
                  <TableCell>
                    {field.required && <Chip label="Required" size="small" color="error" sx={{ mr: 0.5 }} />}
                    {field.dependent && <Chip label="Dependent" size="small" color="warning" />}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Field Values */}
      <Typography variant="h6" fontWeight={600} gutterBottom>
        Field Values
      </Typography>

      {fieldMeta.filter(f => f.name !== 'part_sub_category').map((field) => (
        <Accordion key={field.name}>
          <AccordionSummary expandIcon={<ExpandIcon />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography fontWeight={500}>{field.label}</Typography>
              <Chip label={`${dropdownFields[field.name]?.length || 0} values`} size="small" variant="outlined" />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {(dropdownFields[field.name] || []).map(val => (
                <Chip key={val} label={val} size="small" variant="outlined" />
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>
      ))}

      {/* Dependent Picklist */}
      <Typography variant="h6" sx={{ fontWeight: 600, mt: 3 }} gutterBottom>
        Dependent Picklist: Part Category → Sub-Category
      </Typography>
      <Paper>
        <TableContainer>
          <Table size="small" data-testid="dependency-table">
            <TableHead>
              <TableRow sx={{ bgcolor: 'warning.light' }}>
                <TableCell sx={{ fontWeight: 600 }}>Parent: Part Category</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Child: Sub-Category Values</TableCell>
                <TableCell sx={{ fontWeight: 600 }}>Count</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(subCategoryMap).map(([category, subs]) => (
                <TableRow key={category} hover>
                  <TableCell sx={{ fontWeight: 500 }}>{category}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {subs.map(s => <Chip key={s} label={s} size="small" variant="outlined" />)}
                    </Box>
                  </TableCell>
                  <TableCell>{subs.length}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}
