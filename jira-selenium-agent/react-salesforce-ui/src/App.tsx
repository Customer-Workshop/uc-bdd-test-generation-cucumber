import React, { useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import CarPartsList from './pages/CarPartsList';
import CreateEditForm from './pages/CreateEditForm';
import RecordDetail from './pages/RecordDetail';
import TestData from './pages/TestData';
import DropdownFields from './pages/DropdownFields';
import Layout from './components/Layout';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  if (!isAuthenticated) {
    return <Login onLogin={() => setIsAuthenticated(true)} />;
  }

  return (
    <Layout onLogout={() => setIsAuthenticated(false)}>
      <Routes>
        <Route path="/" element={<Navigate to="/car-parts" replace />} />
        <Route path="/car-parts" element={<CarPartsList />} />
        <Route path="/car-parts/new" element={<CreateEditForm />} />
        <Route path="/car-parts/:id/edit" element={<CreateEditForm />} />
        <Route path="/car-parts/:id" element={<RecordDetail />} />
        <Route path="/test-data" element={<TestData />} />
        <Route path="/dropdown-fields" element={<DropdownFields />} />
        <Route path="*" element={<Navigate to="/car-parts" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
