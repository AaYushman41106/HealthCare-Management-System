import React from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Shield, 
  Activity, 
  User, 
  LogOut, 
  Stethoscope, 
  Calendar, 
  FileText, 
  LayoutDashboard, 
  ClipboardList, 
  Key, 
  Lock,
  Layers,
  BookOpen
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, role, logout, switchPersona } = useAuth();

  const getRoleBadge = (r) => {
    switch (r) {
      case 'ADMIN':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-100 text-rose-700 border border-rose-200">Administrator</span>;
      case 'DOCTOR':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-100 text-teal-800 border border-teal-200">Physician</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">Patient</span>;
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      {/* Top Utility & Persona Switcher Banner */}
      <div className="bg-slate-900 text-slate-300 text-xs px-6 py-2 flex items-center justify-between border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-teal-400" />
          <span className="font-semibold text-slate-200">SecureCare Platform</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-400">Adaptive SDLC Framework (UN SDG 9)</span>
        </div>

        {/* Quick Developer Persona Switcher Buttons */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium mr-1">Switch Persona:</span>
          <button
            onClick={() => switchPersona('admin')}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-all ${
              role === 'ADMIN' 
                ? 'bg-teal-500 text-white font-bold shadow-sm' 
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            🛡️ Admin
          </button>
          <button
            onClick={() => switchPersona('doctor')}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-all ${
              role === 'DOCTOR' 
                ? 'bg-teal-500 text-white font-bold shadow-sm' 
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            🩺 Doctor
          </button>
          <button
            onClick={() => switchPersona('patient')}
            className={`px-2 py-0.5 rounded text-xs font-medium transition-all ${
              role === 'PATIENT' 
                ? 'bg-teal-500 text-white font-bold shadow-sm' 
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
            }`}
          >
            👤 Patient
          </button>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <div 
            onClick={() => setActiveTab('overview')} 
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-600 to-teal-400 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="font-extrabold text-xl tracking-tight text-slate-900 group-hover:text-teal-600 transition-colors">
                Secure<span className="text-teal-600">Care</span>
              </div>
              <div className="text-[10px] uppercase tracking-wider text-slate-400 font-bold -mt-1">
                Healthcare SaaS
              </div>
            </div>
          </div>

          {/* Navigation Links based on role */}
          <nav className="hidden md:flex items-center gap-1">
            {role === 'PATIENT' && (
              <>
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'overview' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" /> Overview
                </button>
                <button
                  onClick={() => setActiveTab('doctors')}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'doctors' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Stethoscope className="w-4 h-4" /> Find Specialists
                </button>
                <button
                  onClick={() => setActiveTab('appointments')}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'appointments' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Calendar className="w-4 h-4" /> My Appointments
                </button>
                <button
                  onClick={() => setActiveTab('records')}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'records' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <FileText className="w-4 h-4" /> Medical Records (EMR)
                </button>
              </>
            )}

            {role === 'DOCTOR' && (
              <>
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'overview' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" /> Clinical Queue
                </button>
                <button
                  onClick={() => setActiveTab('schedule')}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'schedule' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Calendar className="w-4 h-4" /> Schedule
                </button>
                <button
                  onClick={() => setActiveTab('emr')}
                  className={`px-3.5 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'emr' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <ClipboardList className="w-4 h-4" /> Clinical Documentation
                </button>
              </>
            )}

            {role === 'ADMIN' && (
              <>
                <button
                  onClick={() => setActiveTab('overview')}
                  className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'overview' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" /> Executive Overview
                </button>
                <button
                  onClick={() => setActiveTab('security')}
                  className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'security' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Lock className="w-4 h-4" /> Security & Users
                </button>
                <button
                  onClick={() => setActiveTab('audit')}
                  className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'audit' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Key className="w-4 h-4" /> Audit Ledger
                </button>
                <button
                  onClick={() => setActiveTab('jira')}
                  className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                    activeTab === 'jira' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Layers className="w-4 h-4" /> Jira Agile Board
                </button>
              </>
            )}

            <button
              onClick={() => setActiveTab('docs')}
              className={`px-3 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2 ${
                activeTab === 'docs' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`}
            >
              <BookOpen className="w-4 h-4" /> Docs & SDG 9
            </button>
          </nav>
        </div>

        {/* User Info & Logout */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <div className="text-sm font-bold text-slate-800 leading-tight">
                {user?.username}
              </div>
              <div className="mt-0.5">{getRoleBadge(role)}</div>
            </div>
            <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-600 font-bold text-sm">
              {user?.username?.[0]?.toUpperCase() || <User className="w-4 h-4" />}
            </div>
          </div>

          <button
            onClick={logout}
            className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
            title="Sign Out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
