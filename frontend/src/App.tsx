import { useState } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Budget from './pages/Budget';
import Invoices from './pages/Invoices';
import SalesOrders from './pages/SalesOrders';
import Reconciliation from './pages/Reconciliation';
import Proposals from './pages/Proposals';
import Reports from './pages/Reports';
import TrueUp from './pages/TrueUp';
import Settings from './pages/Settings';

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-50">
        <Sidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
        <div className="lg:ml-60 flex flex-col min-h-screen">
          <Header />
          <main className="flex-1 p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/budget" element={<Budget />} />
              <Route path="/invoices" element={<Invoices />} />
              <Route path="/sales-orders" element={<SalesOrders />} />
              <Route path="/reconciliation" element={<Reconciliation />} />
              <Route path="/proposals" element={<Proposals />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/true-up" element={<TrueUp />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
