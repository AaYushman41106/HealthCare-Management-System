import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { 
  Calendar, 
  Clock, 
  User, 
  Stethoscope, 
  FileText, 
  Plus, 
  CheckCircle2, 
  XCircle, 
  AlertCircle, 
  Search, 
  ChevronRight,
  ShieldAlert,
  Pill,
  Sparkles
} from 'lucide-react';

export default function PatientDashboard({ activeTab = 'overview' }) {
  const { user } = useAuth();
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Booking Modal State
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [selectedDoctorId, setSelectedDoctorId] = useState('');
  const [bookingDate, setBookingDate] = useState('');
  const [bookingTime, setBookingTime] = useState('10:00');
  const [bookingReason, setBookingReason] = useState('');
  const [bookingLoading, setBookingLoading] = useState(false);

  // Search filter
  const [searchDoctor, setSearchDoctor] = useState('');

  const fetchData = async () => {
    try {
      setLoading(true);
      const [docsRes, apptsRes, recordsRes] = await Promise.all([
        api.get('/doctors'),
        api.get('/appointments'),
        api.get('/medical-records'),
      ]);
      setDoctors(docsRes.data);
      setAppointments(apptsRes.data);
      setRecords(recordsRes.data);
    } catch (err) {
      console.error('Failed to load patient data:', err);
      setError('Failed to fetch data from API. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleBookAppointment = async (e) => {
    e.preventDefault();
    if (!selectedDoctorId || !bookingDate || !bookingTime) {
      setError('Please select a doctor, consultation date, and time slot.');
      return;
    }

    setError('');
    setSuccess('');
    setBookingLoading(true);

    try {
      await api.post('/appointments', {
        doctor_id: parseInt(selectedDoctorId),
        appointment_date: bookingDate,
        appointment_time: bookingTime,
        reason: bookingReason.trim() || 'Clinical Consultation',
      });
      setSuccess('Consultation successfully scheduled! Awaiting physician confirmation.');
      setShowBookingModal(false);
      setBookingReason('');
      fetchData();
    } catch (err) {
      if (err.response?.status === 409) {
        setError('Schedule Conflict (409): That time slot is already reserved for this specialist or you have an overlapping appointment.');
      } else {
        setError(err.response?.data?.detail || 'Failed to book appointment.');
      }
    } finally {
      setBookingLoading(false);
    }
  };

  const handleCancelAppointment = async (id) => {
    if (!window.confirm('Are you sure you want to cancel this consultation?')) return;
    try {
      await api.patch(`/appointments/${id}/cancel`);
      setSuccess('Appointment cancelled successfully.');
      fetchData();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to cancel appointment.');
    }
  };

  const filteredDoctors = doctors.filter(
    (d) =>
      d.full_name?.toLowerCase().includes(searchDoctor.toLowerCase()) ||
      d.specialization?.toLowerCase().includes(searchDoctor.toLowerCase())
  );

  const upcomingAppt = appointments.find((a) => a.status === 'CONFIRMED' || a.status === 'PENDING');

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
          {/* Header Banner */}
          <div className="bg-gradient-to-r from-teal-800 to-slate-900 rounded-2xl p-8 text-white shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold mb-3 border border-teal-500/30">
                <Sparkles className="w-3.5 h-3.5" /> Patient Health Portal
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight">
                Welcome back, {user?.patient_profile?.full_name || user?.username}!
              </h1>
              <p className="text-slate-300 text-sm mt-1 max-w-xl">
                Manage your consultations, discover board-certified medical specialists, and review confidential EMR diagnostic records.
              </p>
            </div>
            <button
              onClick={() => setShowBookingModal(true)}
              className="py-3 px-5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-extrabold text-sm shadow-md transition-all flex items-center gap-2 shrink-0 hover:scale-105"
            >
              <Plus className="w-4 h-4" /> Book Consultation
            </button>
          </div>

          {/* Metric Cards */}
          <div className="grid sm:grid-cols-3 gap-6">
            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Total Consultations</span>
                <Calendar className="w-5 h-5 text-teal-600" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{appointments.length}</div>
              <p className="text-xs text-slate-500 mt-1">Recorded across all visits</p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Clinical Records</span>
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{records.length}</div>
              <p className="text-xs text-slate-500 mt-1">EMR diagnoses & prescriptions</p>
            </div>

            <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Available Specialists</span>
                <Stethoscope className="w-5 h-5 text-emerald-600" />
              </div>
              <div className="text-3xl font-extrabold text-slate-900">{doctors.length}</div>
              <p className="text-xs text-slate-500 mt-1">Accepting appointments</p>
            </div>
          </div>

          {/* Next Upcoming Consultation */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Clock className="w-5 h-5 text-teal-600" /> Next Upcoming Consultation
              </h2>
            </div>
            {upcomingAppt ? (
              <div className="bg-teal-50/50 border border-teal-100 rounded-xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-teal-600 text-white flex items-center justify-center font-bold text-lg">
                    {upcomingAppt.doctor?.full_name?.[4] || 'Dr'}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">{upcomingAppt.doctor?.full_name}</h3>
                    <p className="text-xs text-teal-700 font-semibold">{upcomingAppt.doctor?.specialization}</p>
                    <p className="text-xs text-slate-500 mt-0.5">
                      📅 {upcomingAppt.appointment_date} at ⏰ {upcomingAppt.appointment_time}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                    upcomingAppt.status === 'CONFIRMED'
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-amber-100 text-amber-800'
                  }`}>
                    {upcomingAppt.status}
                  </span>
                  {upcomingAppt.status === 'PENDING' && (
                    <button
                      onClick={() => handleCancelAppointment(upcomingAppt.id)}
                      className="px-3 py-1 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg transition-colors border border-rose-200"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400 text-sm">
                No upcoming consultations scheduled. Discover specialists and book an appointment today.
              </div>
            )}
          </div>
        </div>
      )}

      {/* SPECIALISTS DIRECTORY TAB */}
      {activeTab === 'doctors' && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-900">Medical Specialists Directory</h2>
              <p className="text-xs text-slate-500 mt-0.5">Board-certified physicians available for clinical consultations</p>
            </div>
            <div className="relative w-full sm:w-72">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search by physician or specialty..."
                value={searchDoctor}
                onChange={(e) => setSearchDoctor(e.target.value)}
                className="w-full pl-9 pr-4 py-2 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDoctors.map((doc) => (
              <div key={doc.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="w-12 h-12 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-600 font-bold text-lg">
                      {doc.full_name?.[4] || 'Dr'}
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800">
                      Available
                    </span>
                  </div>
                  <h3 className="font-extrabold text-slate-900 text-lg">{doc.full_name}</h3>
                  <p className="text-sm font-semibold text-teal-700">{doc.specialization}</p>
                  <p className="text-xs text-slate-400 mt-1 font-mono">License: {doc.license_number}</p>
                  <p className="text-xs text-slate-500 mt-2">📞 {doc.phone || 'Direct clinic booking'}</p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-100">
                  <button
                    onClick={() => {
                      setSelectedDoctorId(doc.id.toString());
                      setShowBookingModal(true);
                    }}
                    className="w-full py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-sm transition-all flex items-center justify-center gap-2"
                  >
                    <Calendar className="w-4 h-4" /> Book Consultation
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* APPOINTMENTS TAB */}
      {activeTab === 'appointments' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-extrabold text-slate-900">My Consultations</h2>
              <p className="text-xs text-slate-500 mt-0.5">Complete chronological itinerary of all consultation requests</p>
            </div>
            <button
              onClick={() => setShowBookingModal(true)}
              className="py-2.5 px-4 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-sm transition-all flex items-center gap-2"
            >
              <Plus className="w-4 h-4" /> Schedule New
            </button>
          </div>

          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-6 py-4">Specialist</th>
                    <th className="px-6 py-4">Specialty</th>
                    <th className="px-6 py-4">Date & Time</th>
                    <th className="px-6 py-4">Reason</th>
                    <th className="px-6 py-4">Status</th>
                    <th className="px-6 py-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {appointments.length > 0 ? (
                    appointments.map((appt) => (
                      <tr key={appt.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="px-6 py-4 font-bold text-slate-900">{appt.doctor?.full_name}</td>
                        <td className="px-6 py-4 text-teal-700 font-medium">{appt.doctor?.specialization}</td>
                        <td className="px-6 py-4 font-mono text-xs text-slate-600">
                          {appt.appointment_date} @ {appt.appointment_time}
                        </td>
                        <td className="px-6 py-4 text-slate-600 max-w-xs truncate">{appt.reason || '-'}</td>
                        <td className="px-6 py-4">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                            appt.status === 'CONFIRMED'
                              ? 'bg-blue-100 text-blue-800'
                              : appt.status === 'COMPLETED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : appt.status === 'CANCELLED'
                              ? 'bg-slate-100 text-slate-600'
                              : 'bg-amber-100 text-amber-800'
                          }`}>
                            {appt.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right">
                          {appt.status === 'PENDING' && (
                            <button
                              onClick={() => handleCancelAppointment(appt.id)}
                              className="px-3 py-1 text-xs font-bold text-rose-600 hover:bg-rose-50 border border-rose-200 rounded-lg transition-colors"
                            >
                              Cancel Booking
                            </button>
                          )}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="6" className="px-6 py-12 text-center text-slate-400">
                        No consultations found. Book an appointment with a specialist above.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* MEDICAL RECORDS TAB */}
      {activeTab === 'records' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-extrabold text-slate-900">Electronic Medical Records (EMR)</h2>
            <p className="text-xs text-slate-500 mt-0.5">Confidential clinical diagnostic records, symptoms, and prescriptions</p>
          </div>

          <div className="space-y-4">
            {records.length > 0 ? (
              records.map((rec) => (
                <div key={rec.id} className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-extrabold text-lg text-slate-900">Record #{rec.id} — {rec.diagnosis}</h3>
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-teal-100 text-teal-800">
                          Authorized EMR
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        Attending Physician: <span className="font-bold text-slate-800">{rec.doctor?.full_name}</span> ({rec.doctor?.specialization})
                      </p>
                    </div>
                    <div className="text-xs text-slate-400 font-mono">
                      📅 {rec.created_at?.slice(0, 10) || 'Verified Visit'}
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-6 mt-4">
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Reported Symptoms</h4>
                      <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200">
                        {rec.symptoms || 'None recorded'}
                      </p>

                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-4 mb-1">Treatment Regimen</h4>
                      <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200">
                        {rec.treatment || 'Standard clinical observation'}
                      </p>
                    </div>

                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-teal-700 mb-1 flex items-center gap-1.5">
                        <Pill className="w-3.5 h-3.5" /> Authorized Prescription
                      </h4>
                      <div className="text-sm font-semibold text-slate-800 bg-teal-50/60 p-3 rounded-xl border border-teal-200">
                        {rec.prescription || 'No pharmaceuticals prescribed.'}
                      </div>

                      {rec.notes && (
                        <>
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mt-4 mb-1">Physician Clinical Notes</h4>
                          <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200">
                            {rec.notes}
                          </p>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
                <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <h3 className="font-bold text-slate-800 text-lg">No Medical Records on File</h3>
                <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
                  Once your physician completes an in-person or virtual consultation, your diagnostic records and prescriptions will appear securely here.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* BOOKING MODAL */}
      {showBookingModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 className="text-lg font-bold text-slate-900">Schedule Clinical Consultation</h3>
              <button
                onClick={() => setShowBookingModal(false)}
                className="w-8 h-8 rounded-lg hover:bg-slate-100 flex items-center justify-center text-slate-400 hover:text-slate-700"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleBookAppointment} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Select Specialist *
                </label>
                <select
                  value={selectedDoctorId}
                  onChange={(e) => setSelectedDoctorId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                  required
                >
                  <option value="">-- Choose a board-certified physician --</option>
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.full_name} — {d.specialization}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Consultation Date *
                  </label>
                  <input
                    type="date"
                    value={bookingDate}
                    onChange={(e) => setBookingDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Time Slot *
                  </label>
                  <select
                    value={bookingTime}
                    onChange={(e) => setBookingTime(e.target.value)}
                    className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                    required
                  >
                    <option value="09:00">09:00 AM</option>
                    <option value="10:00">10:00 AM</option>
                    <option value="11:00">11:00 AM</option>
                    <option value="14:00">02:00 PM</option>
                    <option value="15:00">03:00 PM</option>
                    <option value="16:00">04:00 PM</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Reason for Visit / Symptoms
                </label>
                <textarea
                  value={bookingReason}
                  onChange={(e) => setBookingReason(e.target.value)}
                  placeholder="e.g. Follow-up consultation on blood pressure management"
                  rows="3"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowBookingModal(false)}
                  className="px-4 py-2.5 rounded-xl text-slate-600 hover:bg-slate-100 text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={bookingLoading}
                  className="px-5 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-sm shadow-md transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  {bookingLoading ? 'Reserving...' : 'Confirm Reservation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
