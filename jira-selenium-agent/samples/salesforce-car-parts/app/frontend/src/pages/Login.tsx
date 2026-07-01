import React, { useState } from 'react';
import {
  Box, Card, CardContent, TextField, Button, Typography, Alert,
  Avatar, Container, InputAdornment, IconButton
} from '@mui/material';
import {
  LockOutlined as LockIcon,
  Visibility, VisibilityOff,
  Cloud as CloudIcon
} from '@mui/icons-material';

interface LoginProps {
  onLogin: () => void;
}

export default function Login({ onLogin }: LoginProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username === 'admin@carparts.demo' && password === 'demo1234') {
      setError('');
      onLogin();
    } else {
      setError('Invalid credentials. Use admin@carparts.demo / demo1234');
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 50%, #0d47a1 100%)',
      }}
    >
      <Container maxWidth="sm">
        <Card elevation={8} sx={{ borderRadius: 3 }}>
          <CardContent sx={{ p: 5 }}>
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 3 }}>
              <Avatar sx={{ bgcolor: 'primary.main', width: 56, height: 56, mb: 2 }}>
                <CloudIcon fontSize="large" />
              </Avatar>
              <Typography variant="h4" sx={{ fontWeight: 700, color: 'primary.main' }}>
                Salesforce
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                Car Parts Management - Lightning Experience
              </Typography>
            </Box>

            {error && <Alert severity="error" sx={{ mb: 2 }} data-testid="login-error">{error}</Alert>}

            <form onSubmit={handleSubmit}>
              <TextField
                fullWidth
                label="Username"
                variant="outlined"
                margin="normal"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin@carparts.demo"
                inputProps={{ 'data-testid': 'username-input' }}
                autoFocus
              />
              <TextField
                fullWidth
                label="Password"
                variant="outlined"
                margin="normal"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="demo1234"
                inputProps={{ 'data-testid': 'password-input' }}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                sx={{ mt: 3, py: 1.5, borderRadius: 2, fontWeight: 600 }}
                startIcon={<LockIcon />}
                data-testid="login-button"
              >
                Log In
              </Button>
            </form>

            <Typography variant="caption" display="block" textAlign="center" sx={{ mt: 3 }} color="text.secondary">
              Demo Environment - React + Material UI
            </Typography>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
}
