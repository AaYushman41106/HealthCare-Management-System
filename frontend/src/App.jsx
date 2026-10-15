import React, { useState } from 'react';
import { useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Register from './pages/Register';
import PatientDashboard from './pages/PatientDashboard';
import DoctorDashboard from './pages/DoctorDashboard';
import AdminDashboard from './pages/AdminDashboard';
import Documentation from './pages/Documentation';
import { HeartPulse } from 'lucide-react';

export default function App() {
  const { user, role, isAuthenticated, loading } = useAuth();
  const [isRegistering, setIsRegistering] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  // Loading Screen
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex flex-col items-center justify-center text-white">
        <div className="w-14 h-14 rounded-2xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-teal-400 mb-4 animate-pulse">
          <HeartPulse className="w-8 h-8" />
        </div>
        <div className="text-xl font-bold tracking-tight">SecureCare HMS</div>
        <div className="text-xs text-slate-400 mt-1 font-mono">Initializing secure session...</div>
      </div>
    );
  }

  // Unauthenticated Views
  if (!isAuthenticated) {
    if (isRegistering) {
      return <Register onNavigateToLogin={() => setIsRegistering(false)} />;
    }
    return <Login onNavigateToRegister={() => setIsRegistering(true)} />;
  }

  // Authenticated Portal
  return (
    <div className="min-h-screen bg-brand-bg flex flex-col">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <main className="flex-1">
        {activeTab === 'docs' ? (
          <Documentation />
        ) : role === 'ADMIN' ? (
          <AdminDashboard activeTab={activeTab} />
        ) : role === 'DOCTOR' ? (
          <DoctorDashboard activeTab={activeTab} />
        ) : (
          <PatientDashboard activeTab={activeTab} />
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>
            <span className="font-bold text-slate-700">SecureCare HMS</span> — Adaptive Secure SDLC Framework
          </div>
          <div className="flex items-center gap-4 text-slate-400">
            <span>UN SDG 9: Resilient Digital Infrastructure</span>
            <span>•</span>
            <span>UN SDG 3: Good Health & Well-Being</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
