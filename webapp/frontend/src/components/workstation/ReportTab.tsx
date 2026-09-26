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
  Sparkles,
  Printer
} from 'lucide-react';
import type { ClinicalReport, SleepStudy, StudyMetricsSummary } from '../../types';
import { api } from '../../services/api';

interface ReportTabProps {
  studyId: string;
  study?: SleepStudy;
  metricsSummary?: StudyMetricsSummary | null;
  report: ClinicalReport | null;
  onReportUpdated: (updatedReport: ClinicalReport) => void;
}

export const ReportTab: React.FC<ReportTabProps> = ({
  studyId,
  study,
  metricsSummary,
  report,
  onReportUpdated,
}) => {
  const [physicianNotes, setPhysicianNotes] = useState(report?.physician_notes || '');
  const [savingSignOff, setSavingSignOff] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [viewMode, setViewMode] = useState<'structured' | 'full_narrative'>('structured');
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
  const handlePrintPDF = () => {
    const patientName = study?.patient ? `${study.patient.first_name} ${study.patient.last_name}` : 'بیمار';
    const mrn = study?.patient?.mrn || 'N/A';
    const studyDate = study?.study_date || new Date().toISOString().split('T')[0];
    const duration = study?.duration_minutes ? `${study.duration_minutes} دقیقه` : '--';
    const sqi = metricsSummary ? `${metricsSummary.sqi_score.toFixed(1)} (${metricsSummary.sqi_category})` : '--';

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
      window.print();
      return;
    }

    const htmlContent = `
<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="utf-8">
  <title>گزارش بالینی پلی‌سومنوگرافی — ${patientName} (${mrn})</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;600;700;800;900&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Vazirmatn', Tahoma, sans-serif;
      margin: 0;
      padding: 2cm 1.8cm;
      color: #0f172a;
      background: #ffffff;
      line-height: 1.8;
      font-size: 11pt;
    }
    .header {
      border-bottom: 2px solid #0284c7;
      padding-bottom: 12px;
      margin-bottom: 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand { font-size: 18pt; font-weight: 900; color: #0369a1; }
    .subbrand { font-size: 9pt; color: #64748b; margin-top: 2px; }
    .meta-box {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 12px 16px;
      margin-bottom: 20px;
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 10px;
      font-size: 9.5pt;
    }
    .meta-item { display: flex; flex-direction: column; }
    .meta-label { font-weight: 700; color: #64748b; font-size: 8.5pt; }
    .meta-val { font-weight: 800; color: #0f172a; }
    .section { margin-bottom: 18px; }
    .section-title {
      font-size: 11pt;
      font-weight: 800;
      color: #0369a1;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 4px;
      margin-bottom: 6px;
    }
    .section-body {
      background: #fafafa;
      border-radius: 6px;
      padding: 10px 14px;
      font-size: 10pt;
    }
    .badge {
      display: inline-block;
      background: #e0f2fe;
      color: #0369a1;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 9pt;
      font-weight: 700;
      margin: 3px;
    }
    .rec-item { padding: 4px 0; font-size: 9.5pt; }
    .footer {
      margin-top: 35px;
      border-top: 1px solid #cbd5e1;
      padding-top: 15px;
      display: flex;
      justify-content: space-between;
      font-size: 9pt;
      color: #64748b;
    }
    .signature-box {
      width: 200px;
      text-align: center;
      margin-top: 15px;
      border-top: 1px dashed #94a3b8;
      padding-top: 6px;
      font-weight: 700;
    }
    @media print {
      body { padding: 0; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div>
      <div class="brand">اسلیپ‌لنز (SleepLens)</div>
      <div class="subbrand">سامانه‌ی تصمیم‌یار بالینی طب خواب و پلی‌سومنوگرافی هوشمند</div>
    </div>
    <div style="text-align: left; font-size: 8.5pt; color: #64748b;">
      تاریخ صدور: ${new Date().toLocaleDateString('fa-IR')}<br>
      نسخه گزارش: رسمی / نهایی
    </div>
  </div>

  <div class="meta-box">
    <div class="meta-item"><span class="meta-label">نام بیمار:</span><span class="meta-val">${patientName}</span></div>
    <div class="meta-item"><span class="meta-label">شماره پرونده (MRN):</span><span class="meta-val" dir="ltr">${mrn}</span></div>
    <div class="meta-item"><span class="meta-label">تاریخ آزمایش:</span><span class="meta-val">${studyDate}</span></div>
    <div class="meta-item"><span class="meta-label">مدت زمان ثبت:</span><span class="meta-val">${duration}</span></div>
    <div class="meta-item"><span class="meta-label">شاخص کیفیت خواب (SQI):</span><span class="meta-val" style="color: #0284c7;">${sqi}</span></div>
    <div class="meta-item"><span class="meta-label">وضعیت تایید:</span><span class="meta-val">${report?.is_signed_off ? 'تاییدشده توسط پزشک' : 'پیش‌نویس بالینی'}</span></div>
  </div>

  <div class="section">
    <div class="section-title">۱. خلاصه‌ی اجرایی بالینی (Executive Summary)</div>
    <div class="section-body">${report?.executive_summary || ''}</div>
  </div>

  <div class="section">
    <div class="section-title">۲. ساختار مراحل خواب و تداوم (Architecture & Continuity)</div>
    <div class="section-body">${report?.architecture_findings || ''}</div>
  </div>

  <div class="section">
    <div class="section-title">۳. ارزیابی قلبی‌تنفسی و آپنه (Cardiorespiratory)</div>
    <div class="section-body">${report?.respiratory_and_micro_notes || ''}</div>
  </div>

  <div class="section">
    <div class="section-title">۴. تشخیص‌های افتراقی بالینی</div>
    <div class="section-body">
      ${(report?.differential_diagnoses || []).map(d => `<span class="badge">${d}</span>`).join(' ')}
    </div>
  </div>

  <div class="section">
    <div class="section-title">۵. اقدامات و توصیه‌های درمانی</div>
    <div class="section-body">
      ${(report?.clinical_recommendations || []).map(r => `<div class="rec-item">• ${r}</div>`).join('')}
    </div>
  </div>

  ${report?.physician_notes ? `
  <div class="section">
    <div class="section-title">۶. یادداشت و نظر نهایی پزشک معالج</div>
    <div class="section-body">${report.physician_notes}</div>
  </div>` : ''}

  <div class="footer">
    <div>مرکز ارزیابی اختلالات خواب و پلی‌سومنوگرافی بالینی</div>
    <div class="signature-box">امضا و مهر پزشک متخصص طب خواب</div>
  </div>

  <script>
    window.onload = function() {
      setTimeout(function() {
        window.print();
      }, 300);
    };
  <\/script>
</body>
</html>
    `;

    printWindow.document.open();
    printWindow.document.write(htmlContent);
    printWindow.document.close();
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

        <div className="flex flex-wrap items-center gap-2 no-print">
          <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              type="button"
              onClick={() => setViewMode('structured')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                viewMode === 'structured'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              کارت‌های تفکیکی
            </button>
            <button
              type="button"
              onClick={() => setViewMode('full_narrative')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                viewMode === 'full_narrative'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              متن کامل گزارش (LLM)
            </button>
          </div>

          <button
            type="button"
            onClick={handlePrintPDF}
            className="inline-flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-600/20 transition-all hover:scale-105"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>چاپ / خروجی رسمی PDF</span>
          </button>

          <button
            type="button"
            onClick={handleRegenerate}
            disabled={regenerating}
            className="inline-flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors disabled:opacity-50"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${regenerating ? 'animate-spin' : ''}`} />
            <span>{regenerating ? 'در حال بازتولید...' : 'بازتولید گزارش با آخرین متریک‌ها'}</span>
          </button>
        </div>
      </div>

      {/* Full Narrative View */}
      {viewMode === 'full_narrative' && (
        <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h4 className="text-sm font-black text-slate-900 flex items-center space-x-2 space-x-reverse">
              <Sparkles className="w-4 h-4 text-brand-600" />
              <span>متن مشروح و کامل گزارش بالینی تولیدشده توسط هوش مصنوعی</span>
            </h4>
            <span className="text-xs text-slate-400 font-mono">
              {(report.raw_markdown || report.executive_summary).length.toLocaleString('fa-IR')} کاراکتر
            </span>
          </div>
          <div className="prose prose-slate max-w-none text-sm text-slate-800 leading-relaxed font-sans [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-slate-200 [&_th]:bg-slate-50 [&_th]:p-2.5 [&_td]:border [&_td]:border-slate-200 [&_td]:p-2.5 [&_h1]:text-lg [&_h1]:font-black [&_h2]:text-base [&_h2]:font-bold [&_h2]:mt-6 [&_h2]:mb-2 [&_h2]:text-brand-900 [&_h3]:text-sm [&_h3]:font-bold [&_ul]:list-disc [&_ul]:pr-5 [&_ol]:list-decimal [&_ol]:pr-5">
            <ReactMarkdown>{report.raw_markdown || report.executive_summary}</ReactMarkdown>
          </div>
        </div>
      )}
      {/* Main Report Body - Structured View */}
      {viewMode === 'structured' && (
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
        </div>
      </div>
      )}

      {/* Physician Approval & Notes - Always visible */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-2 space-x-reverse">
            <Edit3 className="w-4 h-4 text-slate-600" />
            <span>یادداشت‌ها و نظر نهایی پزشک معالج</span>
          </h4>
          {report.is_signed_off && (
            <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 flex items-center space-x-1 space-x-reverse">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>گزارش رسماً تایید و امضا شده است</span>
            </span>
          )}
        </div>
        
        <textarea
          rows={3}
          placeholder="نکات بالینی، ملاحظات تکمیلی، یا تغییرات مورد نظر در روند درمان را وارد نمایید..."
          value={physicianNotes}
          onChange={(e) => setPhysicianNotes(e.target.value)}
          className="w-full p-3.5 text-xs rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-right leading-relaxed"
        />

        <div className="flex justify-end pt-1">
          {report.is_signed_off ? (
            <button
              type="button"
              disabled={savingSignOff}
              onClick={() => handleSignOff(false)}
              className="px-6 py-2.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
            >
              {savingSignOff ? 'در حال ثبت...' : 'لغو تایید نهایی (بازگشت به حالت پیش‌نویس)'}
            </button>
          ) : (
            <button
              type="button"
              disabled={savingSignOff}
              onClick={() => handleSignOff(true)}
              className="px-8 py-3 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-600/20 transition-all hover:scale-[1.02]"
            >
              {savingSignOff ? 'در حال امضا...' : 'امضا و تایید نهایی گزارش بالینی'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
