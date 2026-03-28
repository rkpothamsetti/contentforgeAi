import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Pipeline from './pages/Pipeline';
import AgentMonitor from './pages/AgentMonitor';
import ComplianceHub from './pages/ComplianceHub';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/pipeline" element={<Pipeline />} />
            <Route path="/agents" element={<AgentMonitor />} />
            <Route path="/compliance" element={<ComplianceHub />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
