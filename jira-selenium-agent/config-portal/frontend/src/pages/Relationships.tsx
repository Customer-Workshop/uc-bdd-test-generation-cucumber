import React from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, Grid, Card,
  CardContent, Accordion, AccordionSummary, AccordionDetails,
  Divider, Alert
} from '@mui/material';
import {
  AccountTree, ExpandMore, Storage,
  ArrowForward, ArrowDownward
} from '@mui/icons-material';

const objects = [
  {
    api_name: 'Car_Part__c', label: 'Car Part', prefix: 'CP', fields: 13,
    parents: [
      { field: 'Manufacturer__c', ref: 'Manufacturer__r', type: 'Lookup', target: 'Manufacturer__c' },
      { field: 'Warehouse__c', ref: 'Warehouse__r', type: 'Lookup', target: 'Warehouse__c' },
    ],
    children: [
      { name: 'Orders__r', object: 'Order__c', type: 'Master-Detail' },
      { name: 'Warranty_Claims__r', object: 'Warranty_Claim__c', type: 'Lookup' },
    ],
  },
  {
    api_name: 'Manufacturer__c', label: 'Manufacturer', prefix: 'MFR', fields: 7,
    parents: [
      { field: 'Primary_Supplier__c', ref: 'Primary_Supplier__r', type: 'Lookup', target: 'Supplier__c' },
    ],
    children: [
      { name: 'Car_Parts__r', object: 'Car_Part__c', type: 'Lookup' },
    ],
  },
  {
    api_name: 'Warehouse__c', label: 'Warehouse', prefix: 'WH', fields: 6,
    parents: [],
    children: [
      { name: 'Car_Parts__r', object: 'Car_Part__c', type: 'Lookup' },
      { name: 'Orders__r', object: 'Order__c', type: 'Lookup' },
    ],
  },
  {
    api_name: 'Supplier__c', label: 'Supplier', prefix: 'SUP', fields: 6,
    parents: [],
    children: [
      { name: 'Manufacturers__r', object: 'Manufacturer__c', type: 'Lookup' },
    ],
  },
  {
    api_name: 'Order__c', label: 'Order', prefix: 'ORD', fields: 7,
    parents: [
      { field: 'Car_Part__c', ref: 'Car_Part__r', type: 'Master-Detail', target: 'Car_Part__c' },
      { field: 'Ship_From_Warehouse__c', ref: 'Ship_From_Warehouse__r', type: 'Lookup', target: 'Warehouse__c' },
    ],
    children: [
      { name: 'Warranty_Claims__r', object: 'Warranty_Claim__c', type: 'Lookup' },
    ],
  },
  {
    api_name: 'Warranty_Claim__c', label: 'Warranty Claim', prefix: 'WC', fields: 7,
    parents: [
      { field: 'Car_Part__c', ref: 'Car_Part__r', type: 'Lookup', target: 'Car_Part__c' },
      { field: 'Order__c', ref: 'Order__r', type: 'Lookup', target: 'Order__c' },
    ],
    children: [],
  },
];

const testScenarios = [
  { id: 'CAR-1021', tc: 'TC-021', name: 'Parent-to-Child Traversal', type: 'parent_child', priority: 'high', steps: 4 },
  { id: 'CAR-1022', tc: 'TC-022', name: 'Child-to-Parent Traversal', type: 'child_parent', priority: 'high', steps: 5 },
  { id: 'CAR-1023', tc: 'TC-023', name: 'Lookup Relationship Fields', type: 'lookup', priority: 'high', steps: 6 },
  { id: 'CAR-1024', tc: 'TC-024', name: 'Master-Detail Relationship', type: 'master_detail', priority: 'high', steps: 5 },
  { id: 'CAR-1025', tc: 'TC-025', name: 'Custom Object __c API Names', type: 'custom_object', priority: 'medium', steps: 4 },
  { id: 'CAR-1026', tc: 'TC-026', name: 'Cross-Object SOQL Query', type: 'soql', priority: 'high', steps: 5 },
  { id: 'CAR-1027', tc: 'TC-027', name: 'Data Isolation Between Paths', type: 'data_isolation', priority: 'high', steps: 4 },
  { id: 'CAR-1028', tc: 'TC-028', name: 'Multi-Relationship Hub', type: 'data_hub', priority: 'medium', steps: 6 },
];

const apiRules = [
  { rule: 'Field API Name (__c)', desc: 'Stores the Record ID (foreign key)', example: 'Manufacturer__c = "MFR-001"', color: '#1565c0' },
  { rule: 'Relationship Name (__r)', desc: 'Resolves to full parent/child object', example: 'Manufacturer__r.Name = "BorgWarner"', color: '#2e7d32' },
  { rule: 'Custom Object (__c)', desc: 'Defines a custom sObject', example: 'Car_Part__c, Order__c, Warranty_Claim__c', color: '#7b1fa2' },
  { rule: 'Custom Field (__c)', desc: 'Defines a custom field on an object', example: 'Unit_Price__c, Stock_Quantity__c', color: '#e65100' },
];

const typeColor = (type: string) => type === 'Master-Detail' ? 'error' : 'primary';

export default function Relationships() {
  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <AccountTree color="primary" sx={{ mr: 1, fontSize: 28 }} />
        <Typography variant="h5" fontWeight={600}>Salesforce Relationships</Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Multi-relationship data model with Lookup and Master-Detail fields, custom objects (__c), relationship traversal (__r), and cross-object SOQL queries.
      </Typography>

      {/* API Identity Rules */}
      <Alert severity="info" sx={{ mb: 3 }}>
        Salesforce assigns <strong>two distinct API identities</strong> to every relationship field to prevent data blending:
        <strong> __c</strong> (stores the ID) and <strong>__r</strong> (resolves to the full object).
      </Alert>

      <Grid container spacing={2} sx={{ mb: 3 }}>
        {apiRules.map(r => (
          <Grid item xs={12} sm={6} md={3} key={r.rule}>
            <Card sx={{ borderTop: `3px solid ${r.color}`, height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle2" fontWeight={700} sx={{ color: r.color }}>{r.rule}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>{r.desc}</Typography>
                <Chip label={r.example} size="small" variant="outlined" sx={{ fontFamily: 'monospace', fontSize: 11 }} />
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Object Relationship Diagram */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Object Relationship Map (6 Custom Objects)</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap', mb: 2 }}>
          {objects.map((obj, i) => (
            <React.Fragment key={obj.api_name}>
              <Chip
                icon={<Storage />}
                label={`${obj.api_name} (${obj.prefix})`}
                color="primary"
                size="small"
                sx={{ fontFamily: 'monospace' }}
              />
              {i < objects.length - 1 && <ArrowForward fontSize="small" color="action" />}
            </React.Fragment>
          ))}
        </Box>
        <Typography variant="caption" color="text.secondary">
          Each object has a unique key prefix for record IDs. Relationships use __c (field) and __r (traversal) naming convention.
        </Typography>
      </Paper>

      {/* Object Details with Relationships */}
      {objects.map(obj => (
        <Accordion key={obj.api_name} defaultExpanded={obj.api_name === 'Car_Part__c'}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Storage color="primary" fontSize="small" />
              <Typography fontWeight={600}>{obj.api_name}</Typography>
              <Chip label={obj.label} size="small" variant="outlined" />
              <Chip label={`${obj.fields} fields`} size="small" color="info" />
              <Chip label={`${obj.parents.length} parent`} size="small" color="success" />
              <Chip label={`${obj.children.length} child`} size="small" color="warning" />
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {obj.parents.length > 0 && (
              <>
                <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
                  <ArrowForward fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                  Parent Relationships (Lookup / Master-Detail)
                </Typography>
                <TableContainer sx={{ mb: 2 }}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>Field API Name (__c)</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Relationship Name (__r)</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Related To</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {obj.parents.map(rel => (
                        <TableRow key={rel.field}>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: 13 }}>{rel.field}</TableCell>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: 13, color: '#2e7d32', fontWeight: 600 }}>{rel.ref}</TableCell>
                          <TableCell><Chip label={rel.type} size="small" color={typeColor(rel.type)} /></TableCell>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: 13 }}>{rel.target}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
            {obj.children.length > 0 && (
              <>
                <Typography variant="subtitle2" fontWeight={600} sx={{ mb: 1 }}>
                  <ArrowDownward fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                  Child Relationships
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>Relationship Name (__r)</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Child Object</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Type</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {obj.children.map(rel => (
                        <TableRow key={rel.name}>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: 13, color: '#2e7d32', fontWeight: 600 }}>{rel.name}</TableCell>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: 13 }}>{rel.object}</TableCell>
                          <TableCell><Chip label={rel.type} size="small" color={typeColor(rel.type)} /></TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}
            {obj.parents.length === 0 && obj.children.length === 0 && (
              <Typography variant="body2" color="text.secondary">No relationships defined.</Typography>
            )}
          </AccordionDetails>
        </Accordion>
      ))}

      <Divider sx={{ my: 3 }} />

      {/* Test Scenarios */}
      <Typography variant="h6" fontWeight={600} gutterBottom>Relationship Test Scenarios (8)</Typography>
      <TableContainer component={Paper} sx={{ mb: 3 }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Jira ID</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Test Case</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Scenario</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Type</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Priority</TableCell>
              <TableCell align="center" sx={{ color: 'white', fontWeight: 600 }}>Steps</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {testScenarios.map(tc => (
              <TableRow key={tc.id} hover>
                <TableCell sx={{ fontFamily: 'monospace', fontWeight: 600 }}>{tc.id}</TableCell>
                <TableCell sx={{ fontFamily: 'monospace' }}>{tc.tc}</TableCell>
                <TableCell>{tc.name}</TableCell>
                <TableCell>
                  <Chip label={tc.type.replace('_', ' ')} size="small" color="secondary" variant="outlined" />
                </TableCell>
                <TableCell>
                  <Chip label={tc.priority} size="small" color={tc.priority === 'high' ? 'error' : 'warning'} variant="outlined" />
                </TableCell>
                <TableCell align="center">{tc.steps}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* SOQL Examples */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>SOQL Cross-Object Query Examples</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Use the <code>/api/soql</code> endpoint to query across relationships. Parent-to-child uses subqueries, child-to-parent uses dot notation.
        </Typography>
        {[
          { label: 'Child-to-Parent', query: 'SELECT Name, Manufacturer__r.Name, Warehouse__r.Name FROM Car_Part__c', desc: 'Get car parts with manufacturer and warehouse names' },
          { label: 'Parent-to-Child', query: 'SELECT Name, (SELECT Name FROM Orders__r) FROM Car_Part__c', desc: 'Get car parts with their orders' },
          { label: 'Multi-Parent', query: 'SELECT Name, Car_Part__r.Name, Order__r.Name FROM Warranty_Claim__c', desc: 'Traverse two parent objects from warranty claim' },
          { label: 'Chain', query: 'SELECT Name, Primary_Supplier__r.Name, (SELECT Name FROM Car_Parts__r) FROM Manufacturer__c', desc: 'Manufacturer with supplier and car parts' },
        ].map((ex, i) => (
          <Box key={i} sx={{ mb: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
            <Chip label={ex.label} size="small" color="primary" sx={{ mb: 1 }} />
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: 13, mb: 0.5 }}>{ex.query}</Typography>
            <Typography variant="caption" color="text.secondary">{ex.desc}</Typography>
          </Box>
        ))}
      </Paper>

      {/* Traversal Patterns */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" fontWeight={600} gutterBottom>Relationship Traversal Patterns</Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} color="primary">Child-to-Parent (dot notation)</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 1, fontSize: 12 }}>
                Order__c.Car_Part__r.Name{'\n'}
                Order__c.Ship_From_Warehouse__r.Location__c{'\n'}
                Car_Part__c.Manufacturer__r.Country__c
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Up to 5 levels deep. Each __r resolves to the parent record.
              </Typography>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ p: 2 }}>
              <Typography variant="subtitle2" fontWeight={600} color="success.main">Parent-to-Child (subquery)</Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 1, fontSize: 12 }}>
                Car_Part__c &rarr; Orders__r (Master-Detail){'\n'}
                Car_Part__c &rarr; Warranty_Claims__r (Lookup){'\n'}
                Manufacturer__c &rarr; Car_Parts__r (Lookup)
              </Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Returns {"{ totalSize, records[] }"}. Master-Detail enforces cascade delete.
              </Typography>
            </Card>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
}
