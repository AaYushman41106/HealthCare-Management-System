import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Shield, Lock, User, ArrowRight, AlertCircle, CheckCircle2, HeartPulse } from 'lucide-react';

export default function Login({ onNavigateToRegister }) {
  const { login, switchPersona } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Please provide both your identifier and password.');
      return;
    }

    setError('');
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (err) {
      const msg = err.response?.data?.detail || 'Authentication failed. Please check your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handlePersona = async (persona) => {
    setError('');
    setLoading(true);
    try {
      await switchPersona(persona);
    } catch (err) {
      setError(`Failed to switch to ${persona}: ` + (err.response?.data?.detail || err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
      <div className="max-w-4xl w-full grid md:grid-cols-2 bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200">
        
        {/* Left: Brand & SDLC Hero */}
        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-teal-950 p-8 sm:p-12 text-white flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-11 h-11 rounded-xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-teal-400">
                <HeartPulse className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-extrabold tracking-tight">SecureCare</h1>
                <p className="text-xs text-teal-400 font-semibold uppercase tracking-wider">Enterprise HMS</p>
              </div>
            </div>

            <h2 className="text-2xl sm:text-3xl font-extrabold text-white leading-tight mb-4">
              Healthcare, connected and protected.
            </h2>
            <p className="text-slate-300 text-sm leading-relaxed mb-8">
              Unified healthcare operations built upon an Adaptive Secure SDLC framework. Resilient digital infrastructure safeguarding patient clinical privacy and consultations.
            </p>

            <div className="space-y-3">
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Salted bcrypt hashing & stateless HS256 JWT tokens</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Automated 15-minute brute-force account lockout defense</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Role-based access control & strict anti-IDOR boundaries</span>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Aligned with UN SDG 9 (Target 9.c) & UN SDG 3 (Target 3.8)</span>
              </div>
            </div>
          </div>

          {/* Quick Persona Switcher for Evaluation */}
          <div className="mt-8 pt-6 border-t border-slate-700/60">
            <div className="text-xs font-bold uppercase tracking-wider text-teal-400 mb-2">
              ⚡ Quick Developer Persona Switcher
            </div>
            <p className="text-[11px] text-slate-400 mb-3">
              1-click evaluation shortcuts to inspect different role boundaries:
            </p>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handlePersona('admin')}
                className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center justify-center gap-1 transition-all"
              >
                🛡️ Admin
              </button>
              <button
                type="button"
                onClick={() => handlePersona('doctor')}
                className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center justify-center gap-1 transition-all"
              >
                🩺 Doctor
              </button>
              <button
                type="button"
                onClick={() => handlePersona('patient')}
                className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 flex items-center justify-center gap-1 transition-all"
              >
                👤 Patient
              </button>
            </div>
          </div>
        </div>

        {/* Right: Sign In Form */}
        <div className="p-8 sm:p-12 flex flex-col justify-center">
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-slate-900">Sign In to Portal</h3>
            <p className="text-sm text-slate-500 mt-1">
              Enter your clinical or patient credentials to access SecureCare.
            </p>
          </div>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-500" />
              <div>
                <p className="font-semibold">Authentication Notice</p>
                <p className="text-xs text-rose-600 mt-0.5">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Username or Email
              </label>
              <div className="relative">
                <User className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin, dr_priya, or user@example.com"
                  className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 bg-white transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full pl-11 pr-4 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 bg-white transition-all"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-md shadow-teal-600/20 hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50 mt-6"
            >
              {loading ? 'Authenticating...' : 'Access Portal'}
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-slate-200 text-center">
            <p className="text-sm text-slate-500">
              New to SecureCare?{' '}
              <button
                type="button"
                onClick={onNavigateToRegister}
                className="font-bold text-teal-600 hover:text-teal-700 hover:underline"
              >
                Register as Patient
              </button>
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
