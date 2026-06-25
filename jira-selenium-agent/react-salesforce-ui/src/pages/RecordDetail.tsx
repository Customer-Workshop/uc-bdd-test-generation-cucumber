import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, Paper, Button, Chip, Divider, Table,
  TableBody, TableCell, TableRow, Dialog, DialogTitle, DialogContent,
  DialogContentText, DialogActions, Snackbar, Alert
} from '@mui/material';
import {
  ArrowBack as BackIcon, Edit as EditIcon, Delete as DeleteIcon
} from '@mui/icons-material';
import { CarPart, initialCarParts } from '../data/carPartsData';

export default function RecordDetail() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [part, setPart] = useState<CarPart | null>(null);
  const [deleteDialog, setDeleteDialog] = useState(false);
  const [toast, setToast] = useState({ open: false, message: '' });

  useEffect(() => {
    const saved = localStorage.getItem('carParts');
    const parts: CarPart[] = saved ? JSON.parse(saved) : initialCarParts;
    const found = parts.find(p => p.id === id);
    setPart(found || null);
  }, [id]);

  const handleDelete = () => {
    const saved = localStorage.getItem('carParts');
    let parts: CarPart[] = saved ? JSON.parse(saved) : initialCarParts;
    parts = parts.filter(p => p.id !== id);
    localStorage.setItem('carParts', JSON.stringify(parts));
    setToast({ open: true, message: `"${part?.part_name}" deleted successfully` });
    setDeleteDialog(false);
    setTimeout(() => navigate('/car-parts'), 1500);
  };

  if (!part) {
    return (
      <Box>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/car-parts')}>Back</Button>
        <Typography sx={{ mt: 2 }}>Record not found</Typography>
      </Box>
    );
  }

  const fields = [
    { label: 'Part Name', value: part.part_name },
    { label: 'Part Number', value: part.part_number },
    { label: 'Part Category', value: part.part_category },
    { label: 'Part Sub-Category', value: part.part_sub_category },
    { label: 'Manufacturer', value: part.manufacturer },
    { label: 'Condition', value: part.condition },
    { label: 'Vehicle Make', value: part.vehicle_make },
    { label: 'Year Range', value: part.year_range },
    { label: 'Unit Price', value: `$${part.unit_price.toFixed(2)}` },
    { label: 'Stock Quantity', value: String(part.stock_quantity) },
    { label: 'Availability', value: part.availability },
    { label: 'Warehouse Location', value: part.warehouse_location },
    { label: 'Quality Grade', value: part.quality_grade },
    { label: 'Shipping Class', value: part.shipping_class },
    { label: 'Warranty Type', value: part.warranty_type },
    { label: 'Currency', value: part.currency },
    { label: 'Description', value: part.description },
  ];

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/car-parts')} data-testid="back-button">
          Back
        </Button>
        <Typography variant="h5" fontWeight={600} data-testid="record-title">
          {part.part_name}
        </Typography>
        <Chip label={part.id} size="small" variant="outlined" />
      </Box>

      <Paper sx={{ p: 3, mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6" color="primary">Record Details</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/car-parts/${id}/edit`)}
              data-testid="edit-button"
            >
              Edit
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => setDeleteDialog(true)}
              data-testid="delete-button"
            >
              Delete
            </Button>
          </Box>
        </Box>
        <Divider sx={{ mb: 2 }} />

        <Table size="small" data-testid="detail-table">
          <TableBody>
            {fields.map((field) => (
              <TableRow key={field.label}>
                <TableCell sx={{ fontWeight: 600, width: 200, color: 'text.secondary' }}>
                  {field.label}
                </TableCell>
                <TableCell>{field.value || '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)} data-testid="delete-dialog">
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{part.part_name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained" data-testid="confirm-delete">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="success" variant="filled" data-testid="toast-message">
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
