import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import AppShell from './components/layout/AppShell';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Exceptions from './pages/Exceptions';
import ExceptionDetail from './pages/ExceptionDetail';
import Queries from './pages/Queries';
import Remediation from './pages/Remediation';
import Rules from './pages/Rules';
import RiskHeatmap from './pages/RiskHeatmap';
import FraudAnalytics from './pages/FraudAnalytics';
import GST from './pages/GST';
import WorkingCapital from './pages/WorkingCapital';
import DataIngestion from './pages/DataIngestion';
import Reports from './pages/Reports';

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { accessToken } = useAuthStore();
  if (!accessToken) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="exceptions" element={<Exceptions />} />
          <Route path="exceptions/:id" element={<ExceptionDetail />} />
          <Route path="queries" element={<Queries />} />
          <Route path="remediation" element={<Remediation />} />
          <Route path="rules" element={<Rules />} />
          <Route path="risk" element={<RiskHeatmap />} />
          <Route path="fraud" element={<FraudAnalytics />} />
          <Route path="gst" element={<GST />} />
          <Route path="working-capital" element={<WorkingCapital />} />
          <Route path="ingestion" element={<DataIngestion />} />
          <Route path="reports" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
