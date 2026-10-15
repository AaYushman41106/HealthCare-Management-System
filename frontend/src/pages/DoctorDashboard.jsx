import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { 
  CheckCircle2, 
  XCircle, 
  Calendar, 
  Clock, 
  User, 
  FileText, 
  AlertCircle, 
  Stethoscope, 
  Pill,
  ClipboardCheck,
  Check,
  X
} from 'lucide-react';

export default function DoctorDashboard({ activeTab = 'overview' }) {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // EMR Modal State
  const [showEmrModal, setShowEmrModal] = useState(false);
  const [activeApptForEmr, setActiveApptForEmr] = useState(null);
  const [emrData, setEmrData] = useState({
    diagnosis: '',
    symptoms: '',
    treatment: '',
    prescription: '',
    notes: '',
  });
  const [emrLoading, setEmrLoading] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [apptsRes, recordsRes] = await Promise.all([
        api.get('/appointments'),
        api.get('/medical-records'),
      ]);
      setAppointments(apptsRes.data);
      setRecords(recordsRes.data);
    } catch (err) {
      console.error('Failed to load doctor clinical data:', err);
      setError('Failed to fetch assigned clinical data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleUpdateStatus = async (id, newStatus) => {
    setError('');
    setSuccess('');
    try {
      await api.patch(`/appointments/${id}/status`, { status: newStatus });
      setSuccess(`Appointment #${id} updated to ${newStatus}.`);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update consultation status.');
    }
  };

  const handleOpenEmr = (appt) => {
    setActiveApptForEmr(appt);
    setEmrData({
      diagnosis: '',
      symptoms: appt.reason || '',
      treatment: '',
      prescription: '',
      notes: '',
    });
    setShowEmrModal(true);
  };

  const handleSaveEmr = async (e) => {
    e.preventDefault();
    if (!emrData.diagnosis || !activeApptForEmr) {
      setError('Clinical diagnosis is required to complete record.');
      return;
    }

    setEmrLoading(true);
    setError('');
    try {
      await api.post('/medical-records', {
        appointment_id: activeApptForEmr.id,
        diagnosis: emrData.diagnosis.trim(),
        symptoms: emrData.symptoms.trim() || null,
        treatment: emrData.treatment.trim() || null,
        prescription: emrData.prescription.trim() || null,
        notes: emrData.notes.trim() || null,
      });

      setSuccess(`Medical Record for Appointment #${activeApptForEmr.id} successfully created!`);
      setShowEmrModal(false);
      setActiveApptForEmr(null);
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to author medical record.');
    } finally {
      setEmrLoading(false);
    }
  };

  const pendingQueue = appointments.filter((a) => a.status === 'PENDING');
  const confirmedSchedule = appointments.filter((a) => a.status === 'CONFIRMED');
  const completedVisits = appointments.filter((a) => a.status === 'COMPLETED');

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

      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-teal-900 rounded-2xl p-8 text-white shadow-lg mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold mb-3 border border-teal-500/30">
            <Stethoscope className="w-3.5 h-3.5" /> Physician Operational Workspace
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight">
            {user?.doctor_profile?.full_name ? `Dr. ${user.doctor_profile.full_name}` : user?.username}
          </h1>
          <p className="text-slate-300 text-sm mt-1">
            Specialization: <span className="text-teal-300 font-bold">{user?.doctor_profile?.specialization || 'Clinical Specialist'}</span> • License: <span className="font-mono text-slate-400">{user?.doctor_profile?.license_number || 'DOC-VERIFIED'}</span>
          </p>
        </div>

        <div className="flex items-center gap-4">
          <div className="bg-slate-800/80 border border-slate-700 rounded-xl px-5 py-3 text-center">
            <div className="text-2xl font-extrabold text-teal-400">{pendingQueue.length}</div>
            <div className="text-[11px] text-slate-300 font-bold uppercase tracking-wider">Pending Review</div>
          </div>
          <div className="bg-slate-800/80 border border-slate-700 rounded-xl px-5 py-3 text-center">
            <div className="text-2xl font-extrabold text-white">{confirmedSchedule.length}</div>
            <div className="text-[11px] text-slate-300 font-bold uppercase tracking-wider">Scheduled Today</div>
          </div>
        </div>
      </div>

      {/* CLINICAL QUEUE TAB */}
      {(activeTab === 'overview' || activeTab === 'queue') && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Pending Consultation Queue</h2>
              <p className="text-xs text-slate-500">Incoming patient appointments awaiting clinical acceptance</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800">
              {pendingQueue.length} Pending
            </span>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4">Patient</th>
                    <th className="px-6 py-4">Demographics</th>
                    <th className="px-6 py-4">Requested Date/Slot</th>
                    <th className="px-6 py-4">Symptoms / Reason</th>
                    <th className="px-6 py-4 text-right">Clinical Decisions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {pendingQueue.length > 0 ? (
                    pendingQueue.map((appt) => (
                      <tr key={appt.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-bold text-slate-900">{appt.patient?.full_name}</div>
                          <div className="text-xs text-slate-400">ID #{appt.patient_id}</div>
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-600">
                          <div>Gender: {appt.patient?.gender || 'N/A'}</div>
                          <div>DOB: {appt.patient?.date_of_birth || 'N/A'}</div>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs text-teal-800 font-bold">
                          {appt.appointment_date} @ {appt.appointment_time}
                        </td>
                        <td className="px-6 py-4 text-slate-700 max-w-xs">{appt.reason || '-'}</td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleUpdateStatus(appt.id, 'CONFIRMED')}
                              className="px-3 py-1.5 rounded-lg bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-sm transition-all flex items-center gap-1"
                            >
                              <Check className="w-3.5 h-3.5" /> Confirm
                            </button>
                            <button
                              onClick={() => handleUpdateStatus(appt.id, 'REJECTED')}
                              className="px-3 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-xs border border-rose-200 transition-all flex items-center gap-1"
                            >
                              <X className="w-3.5 h-3.5" /> Reject
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="px-6 py-12 text-center text-slate-400">
                        No pending consultations in your clinical queue.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* CONFIRMED SCHEDULE TAB */}
      {(activeTab === 'overview' || activeTab === 'schedule') && (
        <div className="space-y-6 mt-10">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Confirmed Consultations Schedule</h2>
              <p className="text-xs text-slate-500">Upcoming clinical sessions requiring examination or completion</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-800">
              {confirmedSchedule.length} Scheduled
            </span>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4">Patient</th>
                    <th className="px-6 py-4">Scheduled Slot</th>
                    <th className="px-6 py-4">Clinical Chief Complaint</th>
                    <th className="px-6 py-4">Current Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {confirmedSchedule.length > 0 ? (
                    confirmedSchedule.map((appt) => (
                      <tr key={appt.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-6 py-4">
                          <div className="font-bold text-slate-900">{appt.patient?.full_name}</div>
                          <div className="text-xs text-slate-500">📞 {appt.patient?.phone || 'N/A'}</div>
                        </td>
                        <td className="px-6 py-4 font-mono text-xs text-teal-700 font-bold">
                          {appt.appointment_date} @ {appt.appointment_time}
                        </td>
                        <td className="px-6 py-4 text-slate-700 max-w-xs">{appt.reason || '-'}</td>
                        <td className="px-6 py-4">
                          <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-800">
                            {appt.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => handleUpdateStatus(appt.id, 'COMPLETED')}
                              className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm transition-all"
                            >
                              Mark Completed
                            </button>
                            <button
                              onClick={() => {
                                handleUpdateStatus(appt.id, 'COMPLETED');
                                handleOpenEmr(appt);
                              }}
                              className="px-3 py-1.5 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-800 font-bold text-xs border border-teal-200 transition-all flex items-center gap-1"
                            >
                              <ClipboardCheck className="w-3.5 h-3.5" /> Author EMR
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" className="px-6 py-12 text-center text-slate-400">
                        No confirmed consultations on your schedule.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* CLINICAL DOCUMENTATION / EMR TAB */}
      {activeTab === 'emr' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">Authored Medical Records & Prescriptions</h2>
              <p className="text-xs text-slate-500">Historical clinical records and diagnostic documentation authored by you</p>
            </div>
            <span className="text-xs font-bold text-slate-400 font-mono">
              Total Records: {records.length}
            </span>
          </div>

          <div className="space-y-4">
            {records.length > 0 ? (
              records.map((rec) => (
                <div key={rec.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex items-center justify-between pb-4 border-b border-slate-100">
                    <div>
                      <h3 className="font-extrabold text-slate-900 text-lg">
                        Patient: {rec.patient?.full_name} — Diagnosis: {rec.diagnosis}
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Consultation ID: #{rec.appointment_id} • Date: {rec.created_at?.slice(0, 10)}
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-teal-100 text-teal-800">
                      Authorized EMR
                    </span>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mt-4">
                    <div>
                      <div className="text-xs font-bold uppercase text-slate-500 mb-1">Observed Symptoms</div>
                      <div className="text-sm text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200">
                        {rec.symptoms || 'None recorded'}
                      </div>

                      <div className="text-xs font-bold uppercase text-slate-500 mt-4 mb-1">Recommended Treatment</div>
                      <div className="text-sm text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200">
                        {rec.treatment || 'Observation & lifestyle modifications'}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs font-bold uppercase text-teal-700 mb-1 flex items-center gap-1.5">
                        <Pill className="w-3.5 h-3.5" /> Authorized Prescription
                      </div>
                      <div className="text-sm font-semibold text-slate-800 bg-teal-50/60 p-3 rounded-xl border border-teal-200">
                        {rec.prescription || 'No medications prescribed.'}
                      </div>

                      {rec.notes && (
                        <>
                          <div className="text-xs font-bold uppercase text-slate-500 mt-4 mb-1">Confidential Clinical Notes</div>
                          <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200">
                            {rec.notes}
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400">
                No clinical records authored yet. Mark consultations completed to document EMR findings.
              </div>
            )}
          </div>
        </div>
      )}

      {/* AUTHOR EMR MODAL */}
      {showEmrModal && activeApptForEmr && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Author Electronic Medical Record</h3>
                <p className="text-xs text-slate-500">
                  Patient: <span className="font-bold text-slate-800">{activeApptForEmr.patient?.full_name}</span> (Visit #{activeApptForEmr.id})
                </p>
              </div>
              <button
                onClick={() => setShowEmrModal(false)}
                className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSaveEmr} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Clinical Diagnosis *
                </label>
                <input
                  type="text"
                  value={emrData.diagnosis}
                  onChange={(e) => setEmrData({ ...emrData, diagnosis: e.target.value })}
                  placeholder="e.g. Acute Bronchitis / Stage 1 Hypertension"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Observed Symptoms & Findings
                </label>
                <textarea
                  value={emrData.symptoms}
                  onChange={(e) => setEmrData({ ...emrData, symptoms: e.target.value })}
                  rows="2"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Treatment Plan & Care Instructions
                </label>
                <textarea
                  value={emrData.treatment}
                  onChange={(e) => setEmrData({ ...emrData, treatment: e.target.value })}
                  rows="2"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-teal-800 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                  <Pill className="w-3.5 h-3.5" /> Authorized Prescription
                </label>
                <input
                  type="text"
                  value={emrData.prescription}
                  onChange={(e) => setEmrData({ ...emrData, prescription: e.target.value })}
                  placeholder="e.g. Amoxicillin 500mg BID x 7 days, Salbutamol Inhaler PRN"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-teal-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-teal-50/30"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowEmrModal(false)}
                  className="px-4 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={emrLoading}
                  className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {emrLoading ? 'Authoring Record...' : 'Publish Authorized EMR'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
