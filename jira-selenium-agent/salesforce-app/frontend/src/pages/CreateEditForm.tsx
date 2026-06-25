import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box, Typography, Paper, TextField, Button, Grid, FormControl,
  InputLabel, Select, MenuItem, Alert, Snackbar, Divider, Chip
} from '@mui/material';
import { Save as SaveIcon, ArrowBack as BackIcon } from '@mui/icons-material';
import { CarPart, dropdownFields, subCategoryMap, initialCarParts } from '../data/carPartsData';

export default function CreateEditForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = !!id;

  const emptyPart: CarPart = {
    id: '',
    part_name: '',
    part_number: '',
    part_category: '',
    part_sub_category: '',
    manufacturer: '',
    condition: '',
    vehicle_make: '',
    year_range: '',
    unit_price: 0,
    stock_quantity: 0,
    availability: '',
    warehouse_location: '',
    quality_grade: '',
    shipping_class: '',
    warranty_type: '',
    currency: 'USD',
    description: ''
  };

  const [form, setForm] = useState<CarPart>(emptyPart);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  const [subCategories, setSubCategories] = useState<string[]>([]);

  useEffect(() => {
    if (isEdit) {
      const saved = localStorage.getItem('carParts');
      const parts: CarPart[] = saved ? JSON.parse(saved) : initialCarParts;
      const existing = parts.find(p => p.id === id);
      if (existing) {
        setForm(existing);
        setSubCategories(subCategoryMap[existing.part_category] || []);
      }
    }
  }, [id, isEdit]);

  useEffect(() => {
    if (form.part_category) {
      setSubCategories(subCategoryMap[form.part_category] || []);
      if (!isEdit) {
        setForm(prev => ({ ...prev, part_sub_category: '' }));
      }
    }
  }, [form.part_category, isEdit]);

  const handleChange = (field: keyof CarPart, value: string | number) => {
    setForm(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => { const n = { ...prev }; delete n[field]; return n; });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!form.part_name) newErrors.part_name = 'Part Name is required';
    if (!form.part_number) newErrors.part_number = 'Part Number is required';
    if (!form.part_category) newErrors.part_category = 'Part Category is required';
    if (!form.manufacturer) newErrors.manufacturer = 'Manufacturer is required';
    if (!form.condition) newErrors.condition = 'Condition is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      setToast({ open: true, message: 'Please fill in all required fields', severity: 'error' });
      return;
    }

    const saved = localStorage.getItem('carParts');
    let parts: CarPart[] = saved ? JSON.parse(saved) : initialCarParts;

    if (isEdit) {
      parts = parts.map(p => p.id === id ? form : p);
      setToast({ open: true, message: `"${form.part_name}" updated successfully`, severity: 'success' });
    } else {
      const newPart = { ...form, id: `CP-${String(parts.length + 1).padStart(3, '0')}` };
      parts.push(newPart);
      setToast({ open: true, message: `"${form.part_name}" created successfully`, severity: 'success' });
    }

    localStorage.setItem('carParts', JSON.stringify(parts));
    setTimeout(() => navigate('/car-parts'), 1500);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/car-parts')} data-testid="back-button">
          Back
        </Button>
        <Typography variant="h5" fontWeight={600} data-testid="form-title">
          {isEdit ? 'Edit Car Part' : 'New Car Part'}
        </Typography>
        {isEdit && <Chip label={`ID: ${id}`} size="small" variant="outlined" />}
      </Box>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit} data-testid="car-part-form">
          {/* Basic Information */}
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'primary.main' }} gutterBottom>
            Basic Information
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth label="Part Name" required
                value={form.part_name}
                onChange={(e) => handleChange('part_name', e.target.value)}
                error={!!errors.part_name}
                helperText={errors.part_name}
                inputProps={{ 'data-testid': 'input-part-name' }}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth label="Part Number" required
                value={form.part_number}
                onChange={(e) => handleChange('part_number', e.target.value)}
                error={!!errors.part_number}
                helperText={errors.part_number}
                inputProps={{ 'data-testid': 'input-part-number' }}
              />
            </Grid>
          </Grid>

          {/* Category & Classification */}
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'primary.main' }} gutterBottom>
            Category & Classification
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth required error={!!errors.part_category}>
                <InputLabel>Part Category</InputLabel>
                <Select
                  value={form.part_category}
                  label="Part Category"
                  onChange={(e) => handleChange('part_category', e.target.value)}
                  data-testid="select-part-category"
                >
                  {dropdownFields.part_category.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={!form.part_category}>
                <InputLabel>Part Sub-Category (dependent)</InputLabel>
                <Select
                  value={form.part_sub_category}
                  label="Part Sub-Category (dependent)"
                  onChange={(e) => handleChange('part_sub_category', e.target.value)}
                  data-testid="select-part-sub-category"
                >
                  {subCategories.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth required error={!!errors.manufacturer}>
                <InputLabel>Manufacturer</InputLabel>
                <Select
                  value={form.manufacturer}
                  label="Manufacturer"
                  onChange={(e) => handleChange('manufacturer', e.target.value)}
                  data-testid="select-manufacturer"
                >
                  {dropdownFields.manufacturer.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth required error={!!errors.condition}>
                <InputLabel>Condition</InputLabel>
                <Select
                  value={form.condition}
                  label="Condition"
                  onChange={(e) => handleChange('condition', e.target.value)}
                  data-testid="select-condition"
                >
                  {dropdownFields.condition.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Vehicle Make</InputLabel>
                <Select
                  value={form.vehicle_make}
                  label="Vehicle Make"
                  onChange={(e) => handleChange('vehicle_make', e.target.value)}
                  data-testid="select-vehicle-make"
                >
                  {dropdownFields.vehicle_make.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Divider sx={{ my: 2 }} />

          {/* Inventory & Pricing */}
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'primary.main' }} gutterBottom>
            Inventory & Pricing
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth label="Unit Price" type="number"
                value={form.unit_price || ''}
                onChange={(e) => handleChange('unit_price', parseFloat(e.target.value) || 0)}
                InputProps={{ startAdornment: <span style={{ marginRight: 4 }}>$</span> }}
                inputProps={{ 'data-testid': 'input-unit-price', step: '0.01' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth label="Stock Quantity" type="number"
                value={form.stock_quantity || ''}
                onChange={(e) => handleChange('stock_quantity', parseInt(e.target.value) || 0)}
                inputProps={{ 'data-testid': 'input-stock-quantity' }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Year Range</InputLabel>
                <Select
                  value={form.year_range}
                  label="Year Range"
                  onChange={(e) => handleChange('year_range', e.target.value)}
                  data-testid="select-year-range"
                >
                  {dropdownFields.year_range.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {/* Logistics */}
          <Typography variant="subtitle1" sx={{ fontWeight: 600, color: 'primary.main' }} gutterBottom>
            Logistics & Quality
          </Typography>
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Availability</InputLabel>
                <Select
                  value={form.availability}
                  label="Availability"
                  onChange={(e) => handleChange('availability', e.target.value)}
                  data-testid="select-availability"
                >
                  {dropdownFields.availability.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Warehouse Location</InputLabel>
                <Select
                  value={form.warehouse_location}
                  label="Warehouse Location"
                  onChange={(e) => handleChange('warehouse_location', e.target.value)}
                  data-testid="select-warehouse-location"
                >
                  {dropdownFields.warehouse_location.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Quality Grade</InputLabel>
                <Select
                  value={form.quality_grade}
                  label="Quality Grade"
                  onChange={(e) => handleChange('quality_grade', e.target.value)}
                  data-testid="select-quality-grade"
                >
                  {dropdownFields.quality_grade.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Shipping Class</InputLabel>
                <Select
                  value={form.shipping_class}
                  label="Shipping Class"
                  onChange={(e) => handleChange('shipping_class', e.target.value)}
                  data-testid="select-shipping-class"
                >
                  {dropdownFields.shipping_class.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Warranty Type</InputLabel>
                <Select
                  value={form.warranty_type}
                  label="Warranty Type"
                  onChange={(e) => handleChange('warranty_type', e.target.value)}
                  data-testid="select-warranty-type"
                >
                  {dropdownFields.warranty_type.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4}>
              <FormControl fullWidth>
                <InputLabel>Currency</InputLabel>
                <Select
                  value={form.currency}
                  label="Currency"
                  onChange={(e) => handleChange('currency', e.target.value)}
                  data-testid="select-currency"
                >
                  {dropdownFields.currency.map(opt => (
                    <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          {/* Description */}
          <TextField
            fullWidth label="Description" multiline rows={3}
            value={form.description}
            onChange={(e) => handleChange('description', e.target.value)}
            sx={{ mb: 3 }}
            inputProps={{ 'data-testid': 'input-description' }}
          />

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button variant="outlined" onClick={() => navigate('/car-parts')}>
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={<SaveIcon />}
              data-testid="save-button"
            >
              {isEdit ? 'Save Changes' : 'Create Car Part'}
            </Button>
          </Box>
        </form>
      </Paper>

      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity={toast.severity} variant="filled" data-testid="toast-message">
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
