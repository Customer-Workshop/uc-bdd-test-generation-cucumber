import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar, Toolbar, Typography, Drawer, List, ListItem, ListItemButton,
  ListItemIcon, ListItemText, Box, IconButton, Divider, Collapse
} from '@mui/material';
import {
  Dashboard as DashboardIcon, PlayArrow as ExecuteIcon,
  AccountTree as WorkflowIcon, Assessment as ReportsIcon,
  BugReport as JiraIcon, Cloud as CopadoIcon,
  Computer as SeleniumIcon, GitHub as GitHubIcon,
  SmartToy as AIIcon, Link as AppIcon,
  Upload as UploadIcon, TableChart as TraceIcon,
  FindInPage as SelectorIcon, Dns as McpIcon,
  Schema as FlowIcon, Menu as MenuIcon,
  Settings as SettingsIcon, ExpandLess, ExpandMore,
  Api as ApiIcon,
  AccountTree as RelIcon
} from '@mui/icons-material';

const drawerWidth = 250;

const navSections = [
  {
    title: 'Main',
    items: [
      { text: 'Dashboard', path: '/', icon: <DashboardIcon /> },
      { text: 'Workflow', path: '/workflow', icon: <WorkflowIcon /> },
      { text: 'Execute', path: '/execute', icon: <ExecuteIcon /> },
      { text: 'Reports', path: '/report-config', icon: <ReportsIcon /> },
      { text: 'Traceability', path: '/traceability', icon: <TraceIcon /> },
    ]
  },
  {
    title: 'Testing',
    items: [
      { text: 'API Testing', path: '/api-testing', icon: <ApiIcon /> },
      { text: 'Selenium', path: '/selenium-config', icon: <SeleniumIcon /> },
      { text: 'Relationships', path: '/relationships', icon: <RelIcon /> },
    ]
  },
  {
    title: 'Configuration',
    items: [
      { text: 'App URL', path: '/app-configure', icon: <AppIcon /> },
      { text: 'Test Data', path: '/upload-test-data', icon: <UploadIcon /> },
      { text: 'Jira', path: '/jira-config', icon: <JiraIcon /> },
      { text: 'GitHub', path: '/github-config', icon: <GitHubIcon /> },
      { text: 'Copado', path: '/copado-config', icon: <CopadoIcon /> },
      { text: 'AI Model', path: '/ai-model', icon: <AIIcon /> },
    ]
  },
  {
    title: 'Tools',
    items: [
      { text: 'SelectorsHub', path: '/selectorshub-config', icon: <SelectorIcon /> },
      { text: 'MCP Servers', path: '/mcp-servers', icon: <McpIcon /> },
    ]
  },
  {
    title: 'Reference',
    items: [
      { text: 'Flow Diagram', path: '/flow-diagram', icon: <FlowIcon /> },
    ]
  }
];

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    Main: true, Testing: true, Configuration: true, Tools: true, Reference: true
  });

  const toggleSection = (title: string) => {
    setOpenSections(prev => ({ ...prev, [title]: !prev[title] }));
  };

  const drawer = (
    <Box>
      <Toolbar sx={{ px: 2 }}>
        <SettingsIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="subtitle1" fontWeight={700} color="primary">
          Config Portal
        </Typography>
      </Toolbar>
      <Divider />
      {navSections.map((section) => (
        <Box key={section.title}>
          <ListItem disablePadding>
            <ListItemButton onClick={() => toggleSection(section.title)} dense>
              <ListItemText
                primary={section.title}
                primaryTypographyProps={{ variant: 'caption', fontWeight: 600, color: 'text.secondary', textTransform: 'uppercase' }}
              />
              {openSections[section.title] ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
            </ListItemButton>
          </ListItem>
          <Collapse in={openSections[section.title]} timeout="auto">
            <List dense disablePadding>
              {section.items.map((item) => (
                <ListItem key={item.text} disablePadding>
                  <ListItemButton
                    selected={location.pathname === item.path}
                    onClick={() => { navigate(item.path); setMobileOpen(false); }}
                    sx={{ pl: 3 }}
                  >
                    <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.text} primaryTypographyProps={{ fontSize: 13 }} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Collapse>
        </Box>
      ))}
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton color="inherit" edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ mr: 2, display: { sm: 'none' } }}>
            <MenuIcon />
          </IconButton>
          <SettingsIcon sx={{ mr: 1 }} />
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            Automation Configuration Portal
          </Typography>
          <Typography variant="caption" sx={{ opacity: 0.8 }}>
            React + Material UI
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth, flexShrink: 0,
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
        sx={{ display: { xs: 'block', sm: 'none' }, '& .MuiDrawer-paper': { width: drawerWidth } }}
      >
        {drawer}
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8, minHeight: '100vh' }}>
        {children}
      </Box>
    </Box>
  );
}
