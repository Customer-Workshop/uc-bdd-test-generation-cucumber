import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, Button, TextField, InputAdornment, Chip, Paper,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TablePagination, IconButton, Tooltip, Alert, Snackbar, Dialog,
  DialogTitle, DialogContent, DialogContentText, DialogActions,
  FormControl, InputLabel, Select, MenuItem
} from '@mui/material';
import {
  Add as AddIcon, Search as SearchIcon, Edit as EditIcon,
  Delete as DeleteIcon, Visibility as ViewIcon
} from '@mui/icons-material';
import { CarPart, initialCarParts } from '../data/carPartsData';

export default function CarPartsList() {
  const navigate = useNavigate();
  const [parts, setParts] = useState<CarPart[]>(() => {
    const saved = localStorage.getItem('carParts');
    return saved ? JSON.parse(saved) : initialCarParts;
  });
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [deleteDialog, setDeleteDialog] = useState<CarPart | null>(null);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => {
    localStorage.setItem('carParts', JSON.stringify(parts));
  }, [parts]);

  // Listen for storage changes (when new parts are created)
  useEffect(() => {
    const handleStorage = () => {
      const saved = localStorage.getItem('carParts');
      if (saved) setParts(JSON.parse(saved));
    };
    window.addEventListener('storage', handleStorage);
    // Also poll for changes from same-tab updates
    const interval = setInterval(() => {
      const saved = localStorage.getItem('carParts');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (JSON.stringify(parsed) !== JSON.stringify(parts)) {
          setParts(parsed);
        }
      }
    }, 500);
    return () => { window.removeEventListener('storage', handleStorage); clearInterval(interval); };
  }, [parts]);

  const filteredParts = parts.filter((p) => {
    const matchesSearch = !search || 
      p.part_name.toLowerCase().includes(search.toLowerCase()) ||
      p.part_number.toLowerCase().includes(search.toLowerCase()) ||
      p.manufacturer.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = !categoryFilter || p.part_category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const handleDelete = () => {
    if (deleteDialog) {
      setParts(parts.filter(p => p.id !== deleteDialog.id));
      setToast({ open: true, message: `"${deleteDialog.part_name}" deleted successfully`, severity: 'success' });
      setDeleteDialog(null);
    }
  };

  const categories = Array.from(new Set(parts.map(p => p.part_category)));

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" fontWeight={600} data-testid="list-title">
          Car Parts
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/car-parts/new')}
          data-testid="new-button"
        >
          New Car Part
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <TextField
            size="small"
            placeholder="Search parts..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            InputProps={{
              startAdornment: <InputAdornment position="start"><SearchIcon /></InputAdornment>,
            }}
            inputProps={{ 'data-testid': 'search-input' }}
            sx={{ minWidth: 250 }}
          />
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Category Filter</InputLabel>
            <Select
              value={categoryFilter}
              label="Category Filter"
              onChange={(e) => setCategoryFilter(e.target.value)}
              data-testid="category-filter"
            >
              <MenuItem value="">All Categories</MenuItem>
              {categories.map(cat => (
                <MenuItem key={cat} value={cat}>{cat}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <Chip
            label={`${filteredParts.length} records`}
            color="primary"
            variant="outlined"
            size="small"
          />
        </Box>
      </Paper>

      <TableContainer component={Paper} data-testid="parts-table">
        <Table size="small">
          <TableHead>
            <TableRow sx={{ bgcolor: 'primary.main' }}>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Part Name</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Part Number</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Category</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Manufacturer</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Condition</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Price</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Stock</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }}>Availability</TableCell>
              <TableCell sx={{ color: 'white', fontWeight: 600 }} align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredParts
              .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
              .map((part) => (
              <TableRow key={part.id} hover data-testid={`row-${part.id}`}>
                <TableCell>
                  <Typography variant="body2" sx={{ fontWeight: 500, cursor: 'pointer', color: 'primary.main' }}
                    onClick={() => navigate(`/car-parts/${part.id}`)}
                  >
                    {part.part_name}
                  </Typography>
                </TableCell>
                <TableCell>{part.part_number}</TableCell>
                <TableCell>
                  <Chip label={part.part_category} size="small" variant="outlined" />
                </TableCell>
                <TableCell>{part.manufacturer}</TableCell>
                <TableCell>
                  <Chip
                    label={part.condition}
                    size="small"
                    color={part.condition === 'New' ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell>${part.unit_price.toFixed(2)}</TableCell>
                <TableCell>{part.stock_quantity}</TableCell>
                <TableCell>
                  <Chip
                    label={part.availability}
                    size="small"
                    color={part.availability === 'In Stock' ? 'success' : part.availability === 'Low Stock' ? 'warning' : 'error'}
                  />
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="View">
                    <IconButton size="small" onClick={() => navigate(`/car-parts/${part.id}`)} data-testid={`view-${part.id}`}>
                      <ViewIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Edit">
                    <IconButton size="small" onClick={() => navigate(`/car-parts/${part.id}/edit`)} data-testid={`edit-${part.id}`}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Delete">
                    <IconButton size="small" color="error" onClick={() => setDeleteDialog(part)} data-testid={`delete-${part.id}`}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {filteredParts.length === 0 && (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">No car parts found</Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={filteredParts.length}
          page={page}
          onPageChange={(_, p) => setPage(p)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => { setRowsPerPage(parseInt(e.target.value)); setPage(0); }}
        />
      </TableContainer>

      {/* Delete Confirmation Dialog */}
      <Dialog open={!!deleteDialog} onClose={() => setDeleteDialog(null)} data-testid="delete-dialog">
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete "{deleteDialog?.part_name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog(null)}>Cancel</Button>
          <Button onClick={handleDelete} color="error" variant="contained" data-testid="confirm-delete">
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notification */}
      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity={toast.severity} variant="filled" onClose={() => setToast({ ...toast, open: false })} data-testid="toast-message">
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
