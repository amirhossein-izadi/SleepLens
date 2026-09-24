import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  FileCheck2, 
  RotateCcw, 
  CheckCircle2, 
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
      <div className="bg-white rounded-3xl p-12 text-center border border-slate-200">
        <Sparkles className="w-8 h-8 text-slate-300 animate-spin mx-auto mb-3" />
        <p className="text-sm font-bold text-slate-700">مدل هوش مصنوعی در حال نگارش گزارش بالینی است...</p>
      </div>
    );
  }

  const handleSignOff = async (isSigned: boolean) => {
    setSavingSignOff(true);
    try {
      const updated = await api.signOffReport(studyId, isSigned, physicianNotes);
      onReportUpdated(updated);
    } catch (err) {
      alert('خطا در امضای گزارش: ' + String(err));
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
      alert('خطا در بازتولید گزارش: ' + String(err));
    } finally {
      setRegenerating(false);
    }
  };

  return (
    <div className="space-y-6 text-right">
      {/* Report Header Card */}
      <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5 space-x-reverse">
            <h3 className="text-base font-black text-slate-900">گزارش جامع تشخیصی و بالینی طب خواب</h3>
            {report.is_signed_off ? (
              <span className="inline-flex items-center space-x-1 space-x-reverse px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>امضا و تاییدشده توسط پزشک معالج</span>
              </span>
            ) : (
              <span className="inline-flex items-center space-x-1 space-x-reverse px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
                <span>پیش‌نویس بالینی (در انتظار بررسی پزشک)</span>
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            نگارش‌شده بر اساس تحلیل مدل {report.llm_model_name} • آخرین بروزرسانی: {new Date(report.updated_at).toLocaleDateString('fa-IR')}
          </p>
        </div>

        <button
          onClick={handleRegenerate}
          disabled={regenerating}
          className="inline-flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
          <span>{regenerating ? 'در حال بازتولید...' : 'بازتولید گزارش با آخرین متریک‌ها'}</span>
        </button>
      </div>

      {/* Main Report Body */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Right (First in RTL): Report Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Executive Summary */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">۱. خلاصه‌ی اجرایی بالینی (Executive Summary)</h4>
            <div className="text-sm text-slate-800 leading-relaxed bg-slate-50/70 p-4 rounded-2xl border border-slate-100">
              <ReactMarkdown>{report.executive_summary}</ReactMarkdown>
            </div>
          </div>

          {/* Architecture & Continuity */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">۲. ساختار مراحل خواب و تداوم (Architecture & Continuity)</h4>
            <div className="text-sm text-slate-800 leading-relaxed bg-slate-50/70 p-4 rounded-2xl border border-slate-100">
              <ReactMarkdown>{report.architecture_findings}</ReactMarkdown>
            </div>
          </div>

          {/* Respiratory & Microstructure */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">۳. ارزیابی قلبی‌تنفسی و ریزساختارها (Cardiorespiratory)</h4>
            <div className="text-sm text-slate-800 leading-relaxed bg-slate-50/70 p-4 rounded-2xl border border-slate-100">
              <ReactMarkdown>{report.respiratory_and_micro_notes}</ReactMarkdown>
            </div>
          </div>
        </div>

        {/* Left (Second in RTL): Differential Diagnoses & Actionable Recommendations */}
        <div className="space-y-6">
          {/* Diagnoses Card */}
          <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2 space-x-reverse">
              <Stethoscope className="w-4 h-4 text-brand-600" />
              <span>تشخیص‌های افتراقی بالینی</span>
            </h4>
            <div className="space-y-2">
              {report.differential_diagnoses && report.differential_diagnoses.length > 0 ? (
                report.differential_diagnoses.map((d, i) => (
                  <div key={i} className="p-3 rounded-2xl bg-sky-50/80 border border-sky-200/60 text-xs font-bold text-brand-950">
                    {d}
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400">مورد خاصی شناسایی نشد</p>
              )}
            </div>
          </div>

          {/* Actionable Recommendations */}
          <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2 space-x-reverse">
              <CheckSquare className="w-4 h-4 text-emerald-600" />
              <span>اقدامات و توصیه‌های درمانی</span>
            </h4>
            <div className="space-y-2">
              {report.clinical_recommendations && report.clinical_recommendations.length > 0 ? (
                report.clinical_recommendations.map((r, i) => (
                  <div key={i} className="p-3 rounded-2xl bg-emerald-50/70 border border-emerald-200/60 text-xs font-bold text-emerald-950 flex items-start space-x-2.5 space-x-reverse">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    <span>{r}</span>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400">رعایت اصول استاندارد بهداشت خواب</p>
              )}
            </div>
          </div>

          {/* Physician Approval & Notes */}
          <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2 space-x-reverse">
              <Edit3 className="w-4 h-4 text-slate-600" />
              <span>یادداشت‌ها و نظر نهایی پزشک معالج</span>
            </h4>
            
            <textarea
              rows={4}
              placeholder="نکات بالینی، ملاحظات تکمیلی، یا تغییرات مورد نظر در روند درمان را وارد نمایید..."
              value={physicianNotes}
              onChange={(e) => setPhysicianNotes(e.target.value)}
              className="w-full p-3 text-xs rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-right leading-relaxed"
            />

            <div className="pt-2">
              {report.is_signed_off ? (
                <button
                  type="button"
                  disabled={savingSignOff}
                  onClick={() => handleSignOff(false)}
                  className="w-full py-2.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                >
                  {savingSignOff ? 'در حال ثبت...' : 'لغو تایید نهایی (بازگشت به حالت پیش‌نویس)'}
                </button>
              ) : (
                <button
                  type="button"
                  disabled={savingSignOff}
                  onClick={() => handleSignOff(true)}
                  className="w-full py-3 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-600/20 transition-all hover:scale-[1.02]"
                >
                  {savingSignOff ? 'در حال امضا...' : 'امضا و تایید نهایی گزارش بالینی'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
