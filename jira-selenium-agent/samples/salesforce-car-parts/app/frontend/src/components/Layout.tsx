import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemButton,
  ListItemIcon, ListItemText, Box, IconButton, Avatar, Menu, MenuItem,
  Divider, Chip
} from '@mui/material';
import {
  DirectionsCar as CarIcon,
  Add as AddIcon,
  Storage as DataIcon,
  ViewList as FieldsIcon,
  Menu as MenuIcon,
  Logout as LogoutIcon,
  Dashboard as DashboardIcon
} from '@mui/icons-material';

const drawerWidth = 240;

const navItems = [
  { text: 'Car Parts', path: '/car-parts', icon: <CarIcon /> },
  { text: 'New Car Part', path: '/car-parts/new', icon: <AddIcon /> },
  { text: 'Test Data', path: '/test-data', icon: <DataIcon /> },
  { text: 'Dropdown Fields', path: '/dropdown-fields', icon: <FieldsIcon /> },
];

interface LayoutProps {
  children: React.ReactNode;
  onLogout: () => void;
}

export default function Layout({ children, onLogout }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const drawer = (
    <Box>
      <Toolbar sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2 }}>
        <DashboardIcon color="primary" />
        <Typography variant="subtitle1" sx={{ fontWeight: 700, color: 'primary.main' }}>
          Salesforce
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {navItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => { navigate(item.path); setMobileOpen(false); }}
              data-testid={`nav-${item.text.toLowerCase().replace(/\s+/g, '-')}`}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setMobileOpen(!mobileOpen)}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <CarIcon sx={{ mr: 1 }} />
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Car Parts Management
          </Typography>
          <Chip label="Salesforce LWC" size="small" color="info" variant="outlined" sx={{ mr: 2, color: 'white', borderColor: 'white' }} />
          <IconButton color="inherit" onClick={(e) => setAnchorEl(e.currentTarget)}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>A</Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={() => setAnchorEl(null)}
          >
            <MenuItem disabled>
              <Typography variant="body2">admin@carparts.demo</Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={onLogout} data-testid="logout-btn">
              <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
              Logout
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          display: { xs: 'none', sm: 'block' },
          '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        {drawer}
      </Drawer>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        sx={{
          display: { xs: 'block', sm: 'none' },
          '& .MuiDrawer-paper': { width: drawerWidth },
        }}
      >
        {drawer}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8, minHeight: '100vh' }}>
        {children}
      </Box>
    </Box>
  );
}
