import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Workflow from './pages/Workflow';
import Execute from './pages/Execute';
import Reports from './pages/Reports';
import JiraConfig from './pages/JiraConfig';
import CopadoConfig from './pages/CopadoConfig';
import SeleniumConfig from './pages/SeleniumConfig';
import GitHubConfig from './pages/GitHubConfig';
import AIModel from './pages/AIModel';
import AppConfigure from './pages/AppConfigure';
import UploadTestData from './pages/UploadTestData';
import Traceability from './pages/Traceability';
import SelectorsHub from './pages/SelectorsHub';
import MCPServers from './pages/MCPServers';
import FlowDiagram from './pages/FlowDiagram';
import APITesting from './pages/APITesting';
import Relationships from './pages/Relationships';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/workflow" element={<Workflow />} />
        <Route path="/execute" element={<Execute />} />
        <Route path="/report-config" element={<Reports />} />
        <Route path="/jira-config" element={<JiraConfig />} />
        <Route path="/copado-config" element={<CopadoConfig />} />
        <Route path="/selenium-config" element={<SeleniumConfig />} />
        <Route path="/github-config" element={<GitHubConfig />} />
        <Route path="/ai-model" element={<AIModel />} />
        <Route path="/app-configure" element={<AppConfigure />} />
        <Route path="/upload-test-data" element={<UploadTestData />} />
        <Route path="/traceability" element={<Traceability />} />
        <Route path="/selectorshub-config" element={<SelectorsHub />} />
        <Route path="/mcp-servers" element={<MCPServers />} />
        <Route path="/flow-diagram" element={<FlowDiagram />} />
        <Route path="/api-testing" element={<APITesting />} />
        <Route path="/relationships" element={<Relationships />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
