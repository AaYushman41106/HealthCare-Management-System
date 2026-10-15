import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { 
  Shield, 
  Users, 
  Activity, 
  Lock, 
  Key, 
  Layers, 
  Calendar, 
  CheckCircle2, 
  AlertCircle, 
  Search, 
  Download, 
  Unlock, 
  Plus, 
  RefreshCw,
  TrendingUp,
  Stethoscope
} from 'lucide-react';

export default function AdminDashboard({ activeTab = 'overview' }) {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [jiraStatus, setJiraStatus] = useState(null);
  const [jiraIssues, setJiraIssues] = useState([]);
  const [jiraSprints, setJiraSprints] = useState([]);
  const [jiraEpics, setJiraEpics] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Audit filter state
  const [auditSearch, setAuditSearch] = useState('');
  const [auditActionFilter, setAuditActionFilter] = useState('ALL');

  // Create Jira Issue state
  const [showJiraModal, setShowJiraModal] = useState(false);
  const [newIssue, setNewIssue] = useState({
    summary: '',
    description: '',
    issue_type: 'Story',
    priority: 'Medium',
  });
  const [jiraSubmitting, setJiraSubmitting] = useState(false);

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      const [statsRes, usersRes, docsRes, auditsRes] = await Promise.all([
        api.get('/admin/security-stats'),
        api.get('/admin/users'),
        api.get('/admin/doctors'),
        api.get('/admin/audit-logs'),
      ]);
      setStats(statsRes.data);
      setUsers(usersRes.data);
      setDoctors(docsRes.data);
      setAuditLogs(auditsRes.data);

      // Fetch Jira data non-blockingly
      try {
        const [jStatus, jIssues, jSprints, jEpics] = await Promise.all([
          api.get('/integrations/jira/status'),
          api.get('/integrations/jira/issues'),
          api.get('/integrations/jira/sprints'),
          api.get('/integrations/jira/epics'),
        ]);
        setJiraStatus(jStatus.data);
        setJiraIssues(jIssues.data.issues || jIssues.data || []);
        setJiraSprints(jSprints.data.sprints || jSprints.data || []);
        setJiraEpics(jEpics.data.epics || jEpics.data || []);
      } catch (jErr) {
        console.warn('Jira fetch notice:', jErr);
      }
    } catch (err) {
      console.error('Failed to load administrative telemetry:', err);
      setError('Failed to fetch administrative data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleUnlockUser = async (userId, username) => {
    try {
      await api.patch(`/admin/users/${userId}/unlock`);
      setSuccess(`Account for '${username}' has been successfully unlocked.`);
      fetchAdminData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to unlock user.');
    }
  };

  const handleToggleUserActive = async (userId) => {
    try {
      await api.patch(`/admin/users/${userId}/toggle-active`);
      setSuccess('User active status updated.');
      fetchAdminData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update user status.');
    }
  };

  const handleToggleDoctorActive = async (doctorId) => {
    try {
      await api.patch(`/admin/doctors/${doctorId}/toggle-active`);
      setSuccess('Physician scheduling availability updated.');
      fetchAdminData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update physician status.');
    }
  };

  const handleTransitionJiraIssue = async (key, targetStatus) => {
    try {
      await api.post(`/integrations/jira/issues/${key}/transitions`, { target_status: targetStatus });
      setSuccess(`Issue ${key} moved to ${targetStatus}.`);
      fetchAdminData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to transition Jira issue.');
    }
  };

  const handleCreateJiraIssue = async (e) => {
    e.preventDefault();
    if (!newIssue.summary) return;
    setJiraSubmitting(true);
    try {
      await api.post('/integrations/jira/issues', newIssue);
      setSuccess('User story pushed to Jira Cloud successfully!');
      setShowJiraModal(false);
      setNewIssue({ summary: '', description: '', issue_type: 'Story', priority: 'Medium' });
      fetchAdminData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to push issue to Jira Cloud.');
    } finally {
      setJiraSubmitting(false);
    }
  };

  const handleExportAuditCsv = () => {
    if (!auditLogs.length) return;
    const headers = ['ID', 'Timestamp', 'Action', 'Resource', 'Resource ID', 'User ID', 'IP Address', 'Details'];
    const rows = auditLogs.map(l => [
      l.id,
      l.timestamp,
      l.action,
      l.resource_type,
      l.resource_id || '',
      l.user_id || '',
      l.ip_address || '',
      `"${(l.details || '').replace(/"/g, '""')}"`
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `securecare_audit_log_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Filtered audit logs
  const filteredAudits = auditLogs.filter(log => {
    const matchesAction = auditActionFilter === 'ALL' || log.action === auditActionFilter;
    const matchesQuery = !auditSearch || 
      log.details?.toLowerCase().includes(auditSearch.toLowerCase()) ||
      log.action?.toLowerCase().includes(auditSearch.toLowerCase()) ||
      log.ip_address?.toLowerCase().includes(auditSearch.toLowerCase());
    return matchesAction && matchesQuery;
  });

  // Kanban grouped issues
  const kanbanColumns = {
    'To Do': jiraIssues.filter(i => ['To Do', 'Open', 'Backlog'].includes(i.status)),
    'In Progress': jiraIssues.filter(i => i.status === 'In Progress'),
    'In Review': jiraIssues.filter(i => ['In Review', 'Review', 'Under Review'].includes(i.status)),
    'Done': jiraIssues.filter(i => ['Done', 'Resolved', 'Closed'].includes(i.status)),
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Alert Notices */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError('')} className="text-rose-400 hover:text-rose-700 font-bold">×</button>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
            <span>{success}</span>
          </div>
          <button onClick={() => setSuccess('')} className="text-emerald-400 hover:text-emerald-700 font-bold">×</button>
        </div>
      )}

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div className="space-y-8">
          {/* Header */}
          <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 rounded-2xl p-8 text-white shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold mb-3 border border-teal-500/30">
                <Shield className="w-3.5 h-3.5" /> Executive Command & Governance Center
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight">Administrative Operations</h1>
              <p className="text-slate-300 text-sm mt-1 max-w-xl">
                Real-time clinical throughput telemetry, brute-force mitigation monitoring, and agile delivery status.
              </p>
            </div>
            <button
              onClick={fetchAdminData}
              className="py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-bold text-xs border border-slate-700 shadow-sm transition-all flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" /> Refresh Telemetry
            </button>
          </div>

          {/* System Health Indicators */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-emerald-500 animate-pulse shrink-0"></span>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase">Database Engine</div>
                <div className="text-sm font-extrabold text-slate-800">SQLite Connected</div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
              <span className={`w-3 h-3 rounded-full ${jiraStatus?.is_connected ? 'bg-emerald-500' : 'bg-amber-400'} shrink-0`}></span>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase">Jira Cloud API</div>
                <div className="text-sm font-extrabold text-slate-800">
                  {jiraStatus?.is_connected ? 'Synchronized' : 'Offline / Cache'}
                </div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-emerald-500 shrink-0"></span>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase">Auth Service</div>
                <div className="text-sm font-extrabold text-slate-800">bcrypt (12 Rds)</div>
              </div>
            </div>
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center gap-3">
              <span className="w-3 h-3 rounded-full bg-emerald-500 shrink-0"></span>
              <div>
                <div className="text-xs font-bold text-slate-500 uppercase">Audit Logging</div>
                <div className="text-sm font-extrabold text-slate-800">Immutable Ledger</div>
              </div>
            </div>
          </div>

          {/* Executive KPI Cards */}
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-500 uppercase">Registered Users</span>
                <Users className="w-5 h-5 text-teal-600" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{stats?.total_users || users.length}</div>
              <p className="text-xs text-slate-500 mt-1">Patients, doctors & admins</p>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-500 uppercase">Active Physicians</span>
                <Stethoscope className="w-5 h-5 text-blue-600" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{stats?.active_doctors || doctors.length}</div>
              <p className="text-xs text-slate-500 mt-1">Accepting consultations</p>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-500 uppercase">Consultations Total</span>
                <Calendar className="w-5 h-5 text-indigo-600" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{stats?.total_appointments || 0}</div>
              <p className="text-xs text-slate-500 mt-1">{stats?.completed_appointments || 0} completed visits</p>
            </div>

            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-slate-500 uppercase">Locked Accounts</span>
                <Lock className="w-5 h-5 text-rose-600" />
              </div>
              <div className="text-3xl font-extrabold text-rose-600">{stats?.locked_accounts_count || 0}</div>
              <p className="text-xs text-rose-500 mt-1">{stats?.failed_login_events || 0} failed login warnings</p>
            </div>
          </div>

          {/* Recent Audit Log Preview */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="font-bold text-slate-900 text-lg mb-4">Recent Audit Ledger Activity</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase">
                  <tr>
                    <th className="px-4 py-3">Timestamp (UTC)</th>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Resource</th>
                    <th className="px-4 py-3">User ID</th>
                    <th className="px-4 py-3">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-mono">
                  {auditLogs.slice(0, 6).map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50/80">
                      <td className="px-4 py-3 text-slate-500">{log.timestamp}</td>
                      <td className="px-4 py-3 font-bold text-teal-800">{log.action}</td>
                      <td className="px-4 py-3 text-slate-600">{log.resource_type}</td>
                      <td className="px-4 py-3 text-slate-600">#{log.user_id || 'System'}</td>
                      <td className="px-4 py-3 font-sans text-slate-700">{log.details || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SECURITY & USER GOVERNANCE TAB */}
      {activeTab === 'security' && (
        <div className="space-y-8">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-900">User Account Governance & IAM</h2>
            <p className="text-xs text-slate-500 mt-0.5">Manage identity status, inspect failed login counts, and release lockouts</p>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4">User</th>
                    <th className="px-6 py-4">Role</th>
                    <th className="px-6 py-4">Account Status</th>
                    <th className="px-6 py-4">Failed Logins</th>
                    <th className="px-6 py-4">Lockout Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {users.map((u) => {
                    const isLocked = u.locked_until && new Date(u.locked_until) > new Date();
                    return (
                      <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-bold text-slate-900">{u.username}</div>
                          <div className="text-xs text-slate-400">{u.email}</div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700">
                            {u.role}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            u.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                          }`}>
                            {u.is_active ? 'Active' : 'Deactivated'}
                          </span>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs text-slate-700">{u.failed_login_attempts || 0}</td>
                        <td className="px-6 py-4">
                          {isLocked ? (
                            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-700 flex items-center gap-1 w-fit">
                              <Lock className="w-3 h-3" /> Locked
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400">Normal</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right space-x-2">
                          {isLocked && (
                            <button
                              onClick={() => handleUnlockUser(u.id, u.username)}
                              className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-bold transition-all shadow-sm"
                            >
                              Unlock
                            </button>
                          )}
                          {u.id !== user?.id && (
                            <button
                              onClick={() => handleToggleUserActive(u.id)}
                              className="px-3 py-1 border border-slate-300 hover:bg-slate-100 rounded-lg text-xs font-bold text-slate-700 transition-colors"
                            >
                              {u.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Doctor Scheduling Directory */}
          <div className="pt-4">
            <h3 className="text-xl font-bold text-slate-900 mb-4">Physician Availability Governance</h3>
            <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4">Physician</th>
                    <th className="px-6 py-4">Specialization</th>
                    <th className="px-6 py-4">License #</th>
                    <th className="px-6 py-4">Scheduling Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {doctors.map((d) => (
                    <tr key={d.id} className="hover:bg-slate-50/80">
                      <td className="px-6 py-4 font-bold text-slate-900">{d.full_name}</td>
                      <td className="px-6 py-4 text-teal-700 font-semibold">{d.specialization}</td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-600">{d.license_number}</td>
                      <td className="px-6 py-4">
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                          d.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                        }`}>
                          {d.is_active ? 'Available for Patients' : 'Scheduling Disabled'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => handleToggleDoctorActive(d.id)}
                          className="px-3 py-1 border border-slate-300 hover:bg-slate-100 rounded-lg text-xs font-bold text-slate-700"
                        >
                          {d.is_active ? 'Disable' : 'Enable'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* AUDIT LEDGER TAB */}
      {activeTab === 'audit' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-900">Security & Operational Audit Ledger</h2>
              <p className="text-xs text-slate-500 mt-0.5">Immutable record of authentications, data authorizations, and clinical events</p>
            </div>
            <button
              onClick={handleExportAuditCsv}
              className="py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-2 shrink-0"
            >
              <Download className="w-4 h-4" /> Export CSV
            </button>
          </div>

          {/* Search & Filter Bar */}
          <div className="flex flex-col sm:flex-row gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search audit details, IP address, or action..."
                value={auditSearch}
                onChange={(e) => setAuditSearch(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>
            <select
              value={auditActionFilter}
              onChange={(e) => setAuditActionFilter(e.target.value)}
              className="px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
            >
              <option value="ALL">All Actions</option>
              <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
              <option value="LOGIN_FAILURE">LOGIN_FAILURE</option>
              <option value="ACCOUNT_LOCKED">ACCOUNT_LOCKED</option>
              <option value="ACCOUNT_UNLOCKED">ACCOUNT_UNLOCKED</option>
              <option value="APPOINTMENT_CREATED">APPOINTMENT_CREATED</option>
              <option value="APPOINTMENT_CONFIRMED">APPOINTMENT_CONFIRMED</option>
              <option value="MEDICAL_RECORD_CREATED">MEDICAL_RECORD_CREATED</option>
              <option value="MEDICAL_RECORD_VIEWED">MEDICAL_RECORD_VIEWED</option>
              <option value="MEDICAL_RECORD_ACCESS_DENIED">MEDICAL_RECORD_ACCESS_DENIED</option>
            </select>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase font-sans">
                  <tr>
                    <th className="px-4 py-3">ID</th>
                    <th className="px-4 py-3">Timestamp (UTC)</th>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Resource</th>
                    <th className="px-4 py-3">User ID</th>
                    <th className="px-4 py-3">IP Address</th>
                    <th className="px-4 py-3 font-sans">Audit Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredAudits.map((l) => (
                    <tr key={l.id} className="hover:bg-slate-50/80">
                      <td className="px-4 py-3 text-slate-400 font-bold">#{l.id}</td>
                      <td className="px-4 py-3 text-slate-500">{l.timestamp}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          l.action?.includes('FAILURE') || l.action?.includes('DENIED') || l.action?.includes('LOCKED')
                            ? 'bg-rose-100 text-rose-700'
                            : 'bg-teal-100 text-teal-800'
                        }`}>
                          {l.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-600">{l.resource_type}</td>
                      <td className="px-4 py-3 text-slate-600">#{l.user_id || 'System'}</td>
                      <td className="px-4 py-3 text-slate-500">{l.ip_address || '127.0.0.1'}</td>
                      <td className="px-4 py-3 font-sans text-slate-800 max-w-sm">{l.details || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* JIRA KANBAN BOARD & SPRINTS TAB */}
      {activeTab === 'jira' && (
        <div className="space-y-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-900">Atlassian Jira Cloud Agile Kanban Board</h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Target Project: <span className="font-mono font-bold text-teal-700">{jiraStatus?.project_key || 'SCR'}</span> • Host: <span className="text-slate-600 font-mono">{jiraStatus?.base_url}</span>
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowJiraModal(true)}
                className="py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-2"
              >
                <Plus className="w-4 h-4" /> New Story / Task
              </button>
            </div>
          </div>

          {/* Kanban Board Grid */}
          <div className="grid md:grid-cols-4 gap-6">
            {Object.entries(kanbanColumns).map(([colName, items]) => (
              <div key={colName} className="bg-slate-100/70 rounded-2xl p-4 border border-slate-200 flex flex-col">
                <div className="flex items-center justify-between mb-3 px-1">
                  <h3 className="font-extrabold text-slate-800 text-sm">{colName}</h3>
                  <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-white text-slate-600 border border-slate-200">
                    {items.length}
                  </span>
                </div>

                <div className="space-y-3 flex-1 overflow-y-auto max-h-[600px]">
                  {items.map((item) => (
                    <div key={item.key} className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm hover:shadow transition-shadow">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-bold text-teal-700 font-mono">{item.key}</span>
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                          {item.priority}
                        </span>
                      </div>
                      <p className="text-sm font-bold text-slate-800 leading-snug mb-3">{item.summary}</p>
                      
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between">
                        <span className="text-[11px] text-slate-400">👤 {item.assignee || 'Unassigned'}</span>
                        <select
                          value={colName}
                          onChange={(e) => handleTransitionJiraIssue(item.key, e.target.value)}
                          className="text-[11px] font-semibold text-slate-600 bg-slate-50 border border-slate-200 rounded px-1.5 py-0.5 focus:outline-none"
                        >
                          <option value="To Do">To Do</option>
                          <option value="In Progress">In Progress</option>
                          <option value="In Review">In Review</option>
                          <option value="Done">Done</option>
                        </select>
                      </div>
                    </div>
                  ))}

                  {items.length === 0 && (
                    <div className="text-center py-8 text-xs text-slate-400">No issues in {colName}</div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Sprints & Velocity Summary */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <h3 className="font-bold text-slate-900 text-lg mb-2">Sprint Velocity & Burndown (Sprints 1–5)</h3>
            <p className="text-xs text-slate-500 mb-6">Planned vs Completed story points across delivery milestones</p>
            <div className="grid sm:grid-cols-5 gap-4">
              {jiraSprints.map((s, idx) => (
                <div key={idx} className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <div className="text-xs font-bold text-slate-800 mb-1">{s.name}</div>
                  <div className="text-xs text-slate-500 mb-2 truncate" title={s.goal}>{s.goal || 'Sprint Goals'}</div>
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">Planned: {s.planned_points}</span>
                    <span className="font-bold text-teal-700">Done: {s.completed_points}</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 mt-2 overflow-hidden">
                    <div 
                      className="bg-teal-600 h-1.5 rounded-full" 
                      style={{ width: `${Math.min(100, Math.round((s.completed_points / Math.max(1, s.planned_points)) * 100))}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* CREATE JIRA ISSUE MODAL */}
      {showJiraModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">Create Jira Cloud User Story / Task</h3>
              <button
                onClick={() => setShowJiraModal(false)}
                className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateJiraIssue} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Summary / Title *
                </label>
                <input
                  type="text"
                  value={newIssue.summary}
                  onChange={(e) => setNewIssue({ ...newIssue, summary: e.target.value })}
                  placeholder="e.g. Implement MFA verification step"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Description & Acceptance Criteria
                </label>
                <textarea
                  value={newIssue.description}
                  onChange={(e) => setNewIssue({ ...newIssue, description: e.target.value })}
                  rows="3"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Issue Type
                  </label>
                  <select
                    value={newIssue.issue_type}
                    onChange={(e) => setNewIssue({ ...newIssue, issue_type: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                  >
                    <option value="Story">Story</option>
                    <option value="Task">Task</option>
                    <option value="Bug">Bug</option>
                    <option value="Improvement">Improvement</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Priority
                  </label>
                  <select
                    value={newIssue.priority}
                    onChange={(e) => setNewIssue({ ...newIssue, priority: e.target.value })}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                  >
                    <option value="Highest">Highest</option>
                    <option value="High">High</option>
                    <option value="Medium">Medium</option>
                    <option value="Low">Low</option>
                  </select>
                </div>
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowJiraModal(false)}
                  className="px-4 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={jiraSubmitting}
                  className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {jiraSubmitting ? 'Pushing...' : 'Push to Jira Cloud'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
