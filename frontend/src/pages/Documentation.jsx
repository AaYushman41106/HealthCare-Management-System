import React from 'react';
import { Shield, BookOpen, CheckCircle2, Globe, HeartPulse, Layers, Lock } from 'lucide-react';

export default function Documentation() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold mb-3">
          <BookOpen className="w-3.5 h-3.5" /> Technical Documentation & Specifications
        </div>
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">System Architecture & UN SDG Alignment</h1>
        <p className="text-sm text-slate-500 mt-1">
          Adaptive Secure Software Development Life Cycle (SDLC) Framework for High-Assurance Healthcare Systems.
        </p>
      </div>

      {/* UN SDG Alignment Cards */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-teal-900 to-slate-900 rounded-2xl p-6 text-white shadow-md border border-teal-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-teal-500/20 border border-teal-500/30 flex items-center justify-center text-teal-300">
              <Globe className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-extrabold text-lg text-white">UN SDG 9: Industry & Infrastructure</h3>
              <p className="text-xs text-teal-300 font-semibold">Primary Alignment Target: 9.c & 9.4</p>
            </div>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed mb-4">
            Digital healthcare systems are critical societal assets. SecureCare guarantees continuous uptime and tamper-resistance against credential stuffing and unauthorized modifications.
          </p>
          <div className="space-y-2 text-xs text-slate-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
              <span>Resilient Digital Healthcare Infrastructure (Target 9.c)</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
              <span>Iterative Threat Modeling & Adaptive Security Controls (Target 9.4)</span>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-emerald-950 to-slate-900 rounded-2xl p-6 text-white shadow-md border border-emerald-800">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-300">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-extrabold text-lg text-white">UN SDG 3: Good Health & Well-Being</h3>
              <p className="text-xs text-emerald-300 font-semibold">Contextual Goal Target: 3.8</p>
            </div>
          </div>
          <p className="text-sm text-slate-300 leading-relaxed mb-4">
            Universal access to quality healthcare requires both clinical efficiency and ironclad patient privacy. Eliminates consultation double-booking race conditions while guarding diagnostic EMR records.
          </p>
          <div className="space-y-2 text-xs text-slate-300">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Access to Board-Certified Specialists & Consultations (Target 3.8)</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Confidential Electronic Medical Record Privacy & Prescriptions</span>
            </div>
          </div>
        </div>
      </div>

      {/* Security Defense-in-Depth Matrix */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="font-bold text-slate-900 text-lg mb-4 flex items-center gap-2">
          <Lock className="w-5 h-5 text-teal-600" /> Defense-in-Depth Security Matrix
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">Defensive Control</th>
                <th className="px-6 py-3">Technical Implementation</th>
                <th className="px-6 py-3">Threat Mitigated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="px-6 py-4 font-bold text-slate-900">Stateless Authentication</td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">HS256 signed JWT tokens with 60m expiration</td>
                <td className="px-6 py-4 text-teal-800 font-semibold text-xs">Session Hijacking, Replay Attacks</td>
              </tr>
              <tr>
                <td className="px-6 py-4 font-bold text-slate-900">Salted Password Hashing</td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">bcrypt algorithm with 12 adaptive work rounds</td>
                <td className="px-6 py-4 text-teal-800 font-semibold text-xs">Credential Stuffing, Rainbow Tables</td>
              </tr>
              <tr>
                <td className="px-6 py-4 font-bold text-slate-900">Brute-Force Shield</td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">15-minute account lockout after 5 consecutive failures</td>
                <td className="px-6 py-4 text-teal-800 font-semibold text-xs">Automated Password Guessing</td>
              </tr>
              <tr>
                <td className="px-6 py-4 font-bold text-slate-900">Role-Based Access (RBAC)</td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">Granular FastAPI dependency guards (ADMIN, DOCTOR, PATIENT)</td>
                <td className="px-6 py-4 text-teal-800 font-semibold text-xs">Privilege Escalation, Unauthorized Operations</td>
              </tr>
              <tr>
                <td className="px-6 py-4 font-bold text-slate-900">Anti-IDOR Protection</td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">Server-side ownership verification on appointments & EMRs</td>
                <td className="px-6 py-4 text-teal-800 font-semibold text-xs">Insecure Direct Object References</td>
              </tr>
              <tr>
                <td className="px-6 py-4 font-bold text-slate-900">Anti-Collision Guard</td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">Database-level check returning HTTP 409 on overlapping slots</td>
                <td className="px-6 py-4 text-teal-800 font-semibold text-xs">Double-booking Race Conditions</td>
              </tr>
              <tr>
                <td className="px-6 py-4 font-bold text-slate-900">Immutable Audit Trail</td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">Append-only database ledger recording timestamp, user, IP, action</td>
                <td className="px-6 py-4 text-teal-800 font-semibold text-xs">Non-repudiation & Compliance Auditing</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
