import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  FileCheck2, 
  RotateCcw, 
  CheckCircle2, 
  AlertCircle, 
  Stethoscope, 
  CheckSquare, 
  Edit3, 
  ShieldCheck,
  Sparkles
} from 'lucide-react';
import type { ClinicalReport } from '../../types';
import { api } from '../../services/api';

interface ReportTabProps {
  studyId: string;
  report: ClinicalReport | null;
  onReportUpdated: (updatedReport: ClinicalReport) => void;
}

export const ReportTab: React.FC<ReportTabProps> = ({
  studyId,
  report,
  onReportUpdated,
}) => {
  const [physicianNotes, setPhysicianNotes] = useState(report?.physician_notes || '');
  const [savingSignOff, setSavingSignOff] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  if (!report) {
    return (
      <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
        <Sparkles className="w-8 h-8 text-slate-300 animate-spin mx-auto mb-3" />
        <p className="text-sm font-semibold text-slate-700">Clinical report is being generated...</p>
      </div>
    );
  }

  const handleSignOff = async (isSigned: boolean) => {
    setSavingSignOff(true);
    try {
      const updated = await api.signOffReport(studyId, isSigned, physicianNotes);
      onReportUpdated(updated);
    } catch (err) {
      alert('Error signing off report: ' + String(err));
    } finally {
      setSavingSignOff(false);
    }
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      const regenerated = await api.regenerateReport(studyId);
      onReportUpdated(regenerated);
      setPhysicianNotes(regenerated.physician_notes || '');
    } catch (err) {
      alert('Error regenerating report: ' + String(err));
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Report Header Card */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-bold text-slate-900">Comprehensive Clinical Sleep Report</h3>
            {report.is_signed_off ? (
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Physician Approved & Finalized</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
                <span>Clinical Draft (Awaiting Sign-off)</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Synthesized by {report.llm_model_name} • Updated {new Date(report.updated_at).toLocaleString()}
          </p>
        </div>

        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
          <span>{regenerating ? 'Regenerating...' : 'Regenerate with Latest Metrics'}</span>
        </button>
      </div>

      {/* Main Report Body */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Report Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Executive Summary */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">1. Executive Summary</h4>
            <div className="text-sm text-slate-800 leading-relaxed font-serif bg-slate-50/60 p-4 rounded-xl border border-slate-100">
              <ReactMarkdown>{report.executive_summary}</ReactMarkdown>
            </div>
          </div>

          {/* Architecture & Continuity */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">2. Architecture & Continuity Findings</h4>
            <div className="text-sm text-slate-800 leading-relaxed font-serif bg-slate-50/60 p-4 rounded-xl border border-slate-100">
              <ReactMarkdown>{report.architecture_findings}</ReactMarkdown>
            </div>
          </div>

          {/* Respiratory & Microstructure */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">3. Cardiorespiratory & Microstructure</h4>
            <div className="text-sm text-slate-800 leading-relaxed font-serif bg-slate-50/60 p-4 rounded-xl border border-slate-100">
              <ReactMarkdown>{report.respiratory_and_micro_notes}</ReactMarkdown>
            </div>
          </div>
        </div>

        {/* Right: Differential Diagnoses & Actionable Recommendations */}
        <div className="space-y-6">
          {/* Diagnoses Card */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <Stethoscope className="w-4 h-4 text-brand-600" />
              <span>Differential Diagnoses</span>
            </h4>
            <div className="space-y-2">
              {report.differential_diagnoses && report.differential_diagnoses.length > 0 ? (
                report.differential_diagnoses.map((d, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-sky-50/80 border border-sky-200/60 text-xs font-semibold text-brand-900">
                    {d}
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400">None flagged</p>
              )}
            </div>
          </div>

          {/* Actionable Recommendations */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <CheckSquare className="w-4 h-4 text-emerald-600" />
              <span>Recommended Interventions</span>
            </h4>
            <div className="space-y-2">
              {report.clinical_recommendations && report.clinical_recommendations.length > 0 ? (
                report.clinical_recommendations.map((r, i) => (
                  <div key={i} className="p-2.5 rounded-xl bg-emerald-50/70 border border-emerald-200/60 text-xs font-medium text-emerald-950 flex items-start space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400">Standard sleep hygiene</p>
              )}
            </div>
          </div>

          {/* Physician Approval & Notes */}
          <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
              <Edit3 className="w-4 h-4 text-slate-600" />
              <span>Attending Physician Notes</span>
            </h4>
            
            <textarea
              rows={4}
              placeholder="Enter personal observations, clinical caveats, or agreed treatment adjustments..."
              value={physicianNotes}
              onChange={(e) => setPhysicianNotes(e.target.value)}
              className="w-full p-3 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />

            <div className="pt-2">
              {report.is_signed_off ? (
                <button
                  type="button"
                  disabled={savingSignOff}
                  onClick={() => handleSignOff(false)}
                  className="w-full py-2.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                >
                  {savingSignOff ? 'Updating...' : 'Revoke Sign-off (Reopen Draft)'}
                </button>
              ) : (
                <button
                  type="button"
                  disabled={savingSignOff}
                  onClick={() => handleSignOff(true)}
                  className="w-full py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-600/20 transition-all hover:scale-[1.02]"
                >
                  {savingSignOff ? 'Signing...' : 'Sign & Finalize Clinical Report'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
