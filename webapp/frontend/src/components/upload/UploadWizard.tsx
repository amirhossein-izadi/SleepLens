import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  UploadCloud, 
  User, 
  Calendar, 
  FileArchive, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ArrowLeft, 
  ArrowRight,
  Sparkles,
  Layers,
  Activity,
  FileCheck
} from 'lucide-react';
import { api } from '../../services/api';
import type { Patient, StudyStatus } from '../../types';

interface UploadWizardProps {
  onCancel: () => void;
  onStudyReady: (studyId: string) => void;
}

export const UploadWizard: React.FC<UploadWizardProps> = ({ onCancel, onStudyReady }) => {
  const [step, setStep] = useState<'patient' | 'upload' | 'processing'>('patient');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loadingPatients, setLoadingPatients] = useState(true);

  // Selected or New Patient State
  const [isNewPatient, setIsNewPatient] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [newPatient, setNewPatient] = useState({
    mrn: '',
    first_name: '',
    last_name: '',
    birth_date: '1985-06-15',
    biological_sex: 'male',
    medical_history: 'شکایت از خواب آلودگی مفرط روزانه، بیداری‌های مکرر شبانه و خروپف متناوب.',
  });

  // Upload State
  const [studyType, setStudyType] = useState('full_psg');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Processing Stepper State
  const [activeStudyId, setActiveStudyId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<StudyStatus>('uploaded');
  const [statusMessage, setStatusMessage] = useState('در حال آماده‌سازی نشست پردازش آزمایش...');

  useEffect(() => {
    api.getPatients()
      .then((data) => {
        setPatients(data);
        if (data.length > 0) {
          setSelectedPatientId(data[0].id);
        } else {
          setIsNewPatient(true);
        }
      })
      .catch(() => setIsNewPatient(true))
      .finally(() => setLoadingPatients(false));
  }, []);

  useEffect(() => {
    if (step !== 'processing' || !activeStudyId) return;

    const interval = setInterval(async () => {
      try {
        const statusData = await api.getStudyStatus(activeStudyId);
        setProcessingStatus(statusData.status);

        if (statusData.status === 'extracting') {
          setStatusMessage('در حال بازگشایی امن فایل زیپ و فهرست‌بندی گزارش‌های اپوک...');
        } else if (statusData.status === 'staging') {
          setStatusMessage('مدل هوش مصنوعی در حال پیش‌بینی مراحل خواب اپوک‌های ۳۰ ثانیه‌ای...');
        } else if (statusData.status === 'computing_metrics') {
          setStatusMessage('در حال استخراج متریک‌های ۷گانه و محاسبه شاخص کیفیت خواب (SQI)...');
        } else if (statusData.status === 'generating_report') {
          setStatusMessage('مدل زبانی OpenCode در حال تدوین گزارش تشخیصی و توصیه‌های بالینی...');
        } else if (statusData.status === 'completed') {
          setStatusMessage('پردازش با موفقیت به پایان رسید! انتقال به میز کار بالینی...');
          clearInterval(interval);
          setTimeout(() => {
            onStudyReady(activeStudyId);
          }, 1200);
        } else if (statusData.status === 'failed') {
          setError(statusData.error_log || 'پردازش پرونده با خطا مواجه شد.');
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Status poll error:', err);
      }
    }, 800);

    return () => clearInterval(interval);
  }, [step, activeStudyId, onStudyReady]);

  const handlePatientSubmit = async () => {
    setError(null);
    if (isNewPatient) {
      if (!newPatient.first_name || !newPatient.last_name || !newPatient.mrn) {
        setError('لطفاً نام، نام خانوادگی و شماره پرونده (MRN) بیمار را وارد نمایید.');
        return;
      }
      try {
        const created = await api.createPatient(newPatient);
        setSelectedPatientId(created.id);
        setStep('upload');
      } catch (err: unknown) {
        let msg = 'ثبت بیمار با خطا مواجه شد.';
        if (axios.isAxiosError(err) && err.response?.data?.error) {
          const apiErr = err.response.data.error;
          if (apiErr.details && apiErr.details.length > 0) {
            const firstDetail = apiErr.details[0];
            if (typeof firstDetail === 'object' && firstDetail !== null && 'message' in firstDetail) {
              const detailMsg = String(firstDetail.message);
              if (detailMsg.includes('already exists')) {
                msg = `بیماری با شماره پرونده "${newPatient.mrn}" از قبل در سیستم ثبت شده است. لطفاً آن را از لیست بیماران موجود انتخاب کنید یا شماره پرونده جدیدی وارد فرمایید.`;
              } else {
                msg = detailMsg;
              }
            }
          } else if (apiErr.message) {
            msg = apiErr.message;
          }
        } else if (err instanceof Error) {
          msg = err.message;
        }
        setError(msg);
      }
    } else {
      if (!selectedPatientId) {
        setError('لطفاً یک بیمار را از فهرست انتخاب فرمایید.');
        return;
      }
      setStep('upload');
    }
  };

  const handleUploadSubmit = async () => {
    setError(null);
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('patient_id', selectedPatientId);
      formData.append('study_type', studyType);
      formData.append('study_date', new Date().toISOString().split('T')[0]);

      if (selectedFile) {
        formData.append('raw_archive', selectedFile);
      }

      const res = await api.uploadStudy(formData);
      setActiveStudyId(res.study_id);
      setProcessingStatus(res.status);
      setStep('processing');
    } catch (err: unknown) {
      let msg = 'ارسال و ثبت آزمایش با خطا مواجه شد.';
      if (axios.isAxiosError(err) && err.response?.data?.error?.message) {
        msg = err.response.data.error.message;
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-3xl border border-slate-200 shadow-xl overflow-hidden">
      {/* Wizard Header */}
      <div className="bg-gradient-to-l from-slate-950 via-slate-900 to-brand-950 p-6 text-white flex items-center justify-between">
        <div>
          <h2 className="text-xl font-black flex items-center space-x-2.5 space-x-reverse">
            <UploadCloud className="w-5 h-5 text-sky-400" />
            <span>بارگذاری و ثبت آزمایش خواب جدید</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            استخراج خودکار زیپ، استیجینگ مراحل خواب با هوش مصنوعی، محاسبه متریک‌های SQI و تدوین گزارش بالینی
          </p>
        </div>
        <div className="flex items-center space-x-2 space-x-reverse text-xs font-bold">
          <span className={`px-2.5 py-1 rounded-md ${step === 'patient' ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400'}`}>۱. مشخصات بیمار</span>
          <span className={`px-2.5 py-1 rounded-md ${step === 'upload' ? 'bg-brand-600 text-white' : 'bg-slate-800 text-slate-400'}`}>۲. بارگذاری فایل</span>
          <span className={`px-2.5 py-1 rounded-md ${step === 'processing' ? 'bg-emerald-600 text-white' : 'bg-slate-800 text-slate-400'}`}>۳. پایپ‌لاین AI</span>
        </div>
      </div>

      <div className="p-6">
        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-bold flex items-start space-x-2.5 space-x-reverse">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* STEP 1: PATIENT SELECTION */}
        {step === 'patient' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="text-sm font-black text-slate-800">تعیین بیمار پرونده</span>
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setIsNewPatient(!isNewPatient);
                }}
                className="text-xs font-bold text-brand-600 hover:text-brand-700 hover:underline"
              >
                {isNewPatient ? '← انتخاب از لیست بیماران موجود' : '+ ثبت بیمار جدید'}
              </button>
            </div>

            {isNewPatient ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1.5">نام بیمار</label>
                  <input
                    type="text"
                    placeholder="مثال: مریم"
                    value={newPatient.first_name}
                    onChange={(e) => setNewPatient({ ...newPatient, first_name: e.target.value })}
                    className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1.5">نام خانوادگی</label>
                  <input
                    type="text"
                    placeholder="مثال: رادپور"
                    value={newPatient.last_name}
                    onChange={(e) => setNewPatient({ ...newPatient, last_name: e.target.value })}
                    className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1.5">شماره پرونده پزشکی (MRN)</label>
                  <input
                    type="text"
                    placeholder="مثال: MRN-88120"
                    value={newPatient.mrn}
                    onChange={(e) => setNewPatient({ ...newPatient, mrn: e.target.value })}
                    className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 font-mono text-left"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-600 mb-1.5">جنسیت بیولوژیکی</label>
                  <select
                    value={newPatient.biological_sex}
                    onChange={(e) => setNewPatient({ ...newPatient, biological_sex: e.target.value })}
                    className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  >
                    <option value="male">مرد (Male)</option>
                    <option value="female">زن (Female)</option>
                    <option value="other">نامشخص / سایر</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-slate-600 mb-1.5">شرح حال بالینی و علائم اصلی خواب (اختیاری)</label>
                  <textarea
                    rows={2}
                    placeholder="شکایت از آپنه، خروپف، بیداری‌های شبانه یا خستگی روزانه..."
                    value={newPatient.medical_history}
                    onChange={(e) => setNewPatient({ ...newPatient, medical_history: e.target.value })}
                    className="w-full px-3.5 py-2 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1.5">انتخاب بیمار ثبت‌شده</label>
                {loadingPatients ? (
                  <div className="p-3 text-sm text-slate-400 flex items-center space-x-2 space-x-reverse">
                    <Loader2 className="w-4 h-4 animate-spin text-brand-600" />
                    <span>در حال بارگذاری لیست بیماران...</span>
                  </div>
                ) : (
                  <select
                    value={selectedPatientId}
                    onChange={(e) => setSelectedPatientId(e.target.value)}
                    className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  >
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.first_name} {p.last_name} — شماره پرونده: {p.mrn} ({p.biological_sex === 'female' ? 'زن' : 'مرد'})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}

            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800"
              >
                انصراف و بازگشت
              </button>
              <button
                type="button"
                onClick={handlePatientSubmit}
                className="inline-flex items-center space-x-2 space-x-reverse px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-600/20 transition-all hover:scale-105"
              >
                <span>مرحله بعد: بارگذاری فایل</span>
                <ArrowLeft className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: FILE UPLOAD */}
        {step === 'upload' && (
          <div className="space-y-5">
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1.5">نوع محیط ضبط تست خواب</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'full_psg', label: 'پلی‌سومنوگرافی کامل کلینیکی (PSG)' },
                  { id: 'cassette_home', label: 'تست خانگی کاست (Home)' },
                  { id: 'telemetry_hospital', label: 'تله‌متری بیمارستانی (Hospital)' },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setStudyType(t.id)}
                    className={`p-3 rounded-2xl border text-xs font-bold text-center transition-all ${
                      studyType === t.id
                        ? 'border-brand-600 bg-brand-50 text-brand-700 shadow-sm'
                        : 'border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Dropzone */}
            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1.5">بارگذاری آرشیو داده‌های بیمار</label>
              <div className="border-2 border-dashed border-slate-200 hover:border-brand-500 rounded-3xl p-6 text-center transition-all bg-slate-50/50">
                <FileArchive className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-bold text-slate-800">
                  {selectedFile ? selectedFile.name : 'فایل زیپ گزارش‌های بیمار را اینجا رها کنید'}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  پشتیبانی از فایل‌های زیپ، گزارش‌های اپوک ۳۰ ثانیه‌ای، فایل‌های .edf، .epf یا آرایه‌های npz (تا ۵۰۰ مگابایت)
                </p>
                
                <input
                  type="file"
                  id="archive-upload"
                  accept=".zip,.edf,.epf,.npz"
                  onChange={(e) => {
                    const file = e.target.files?.[0] || null;
                    if (file) {
                      const validExts = ['.zip', '.edf', '.epf', '.npz'];
                      const isExtValid = validExts.some((ext) => file.name.toLowerCase().endsWith(ext));
                      if (!isExtValid) {
                        setError('فرمت فایل نامعتبر است. لطفاً یک فایل زیپ حاوی گزارش‌های اپوک یا دیتای پلی‌سومنوگرافی (.edf / .epf) انتخاب فرمایید.');
                        setSelectedFile(null);
                        return;
                      }
                      setError(null);
                      setSelectedFile(file);
                    }
                  }}
                  className="hidden"
                />
                
                <div className="mt-4 flex items-center justify-center space-x-3 space-x-reverse">
                  <label
                    htmlFor="archive-upload"
                    className="inline-flex items-center space-x-1.5 space-x-reverse px-4 py-2 rounded-xl text-xs font-bold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-sm cursor-pointer transition-all"
                  >
                    <span>انتخاب فایل از رایانه</span>
                  </label>
                  
                  <span className="text-xs text-slate-400">یا</span>
                  
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null);
                      handleUploadSubmit();
                    }}
                    className="inline-flex items-center space-x-1.5 space-x-reverse px-4 py-2 rounded-xl text-xs font-bold bg-sky-50 border border-sky-200 text-brand-700 hover:bg-sky-100 shadow-sm transition-all"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                    <span>اجرای دیتای نمونه ۹۰ دقیقه‌ای (تست فوری)</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setStep('patient')}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-800"
              >
                بازگشت به مرحله قبل
              </button>
              
              <button
                type="button"
                disabled={submitting}
                onClick={handleUploadSubmit}
                className="inline-flex items-center space-x-2 space-x-reverse px-6 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-600/20 disabled:opacity-50 transition-all hover:scale-105"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>در حال بارگذاری و شروع...</span>
                  </>
                ) : (
                  <>
                    <span>شروع پایپ‌لاین تحلیل هوشمند</span>
                    <ArrowLeft className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: REAL-TIME PIPELINE PROGRESS */}
        {step === 'processing' && (
          <div className="py-6 space-y-6 text-center">
            {processingStatus === 'failed' ? (
              <div className="space-y-4">
                <div className="w-16 h-16 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto shadow-md shadow-rose-500/10">
                  <AlertCircle className="w-8 h-8 text-rose-600" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-rose-900">پردازش پایپ‌لاین با خطا مواجه شد</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    فایل ارسالی یا محتوای آن با استانداردهای پلی‌سومنوگرافی سیستم مطابقت ندارد.
                  </p>
                </div>
                <div className="max-w-md mx-auto p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-mono text-right break-words leading-relaxed">
                  {error || 'فرمت فایل معتبر نیست: لطفاً مطمئن شوید که یک فایل استاندارد ZIP یا EDF ارسال می‌کنید.'}
                </div>
                <div className="flex items-center justify-center space-x-3 space-x-reverse pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setError(null);
                      setStep('upload');
                      setProcessingStatus('uploaded');
                      setSelectedFile(null);
                    }}
                    className="px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-all hover:scale-105"
                  >
                    انتخاب فایل دیگر و تلاش مجدد
                  </button>
                  <button
                    type="button"
                    onClick={onCancel}
                    className="px-4 py-2.5 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
                  >
                    انصراف و بازگشت به داشبورد
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="w-16 h-16 rounded-2xl bg-brand-50 border border-brand-200 text-brand-600 flex items-center justify-center mx-auto shadow-md shadow-brand-500/10">
                  {processingStatus === 'completed' ? (
                    <CheckCircle2 className="w-8 h-8 text-emerald-600 animate-bounce" />
                  ) : (
                    <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-black text-slate-900">
                    {processingStatus === 'completed' ? 'پرونده آماده بررسی و تحلیل بالینی است!' : 'در حال اجرای مراحل هوشمند تحلیل خواب'}
                  </h3>
                  <p className="text-xs font-medium text-slate-500 mt-1 max-w-md mx-auto">
                    {statusMessage}
                  </p>
                </div>

                {/* Stepper Progress Visualizer */}
                <div className="max-w-md mx-auto space-y-3 text-right">
                  {[
                    { label: 'بازگشایی امن زیپ و فهرست‌بندی فایل‌های ضبط', activeStatus: ['extracting', 'staging', 'computing_metrics', 'generating_report', 'completed'] },
                    { label: 'تعیین ۵ مرحله خواب AASM برای اپوک‌های ۳۰ ثانیه‌ای', activeStatus: ['staging', 'computing_metrics', 'generating_report', 'completed'] },
                    { label: 'استخراج متریک‌های ۷گانه و محاسبه شاخص SQI', activeStatus: ['computing_metrics', 'generating_report', 'completed'] },
                    { label: 'تدوین گزارش بالینی تشخیصی توسط مدل زبانی OpenCode', activeStatus: ['generating_report', 'completed'] },
                  ].map((s, idx) => {
                    const isPassed = s.activeStatus.includes(processingStatus);
                    const isCurrent = s.activeStatus[0] === processingStatus;

                    return (
                      <div key={idx} className="flex items-center space-x-3 space-x-reverse text-xs">
                        {isPassed && !isCurrent ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                        ) : isCurrent ? (
                          <Loader2 className="w-4 h-4 text-brand-600 animate-spin flex-shrink-0" />
                        ) : (
                          <div className="w-4 h-4 rounded-full border border-slate-300 flex-shrink-0" />
                        )}
                        <span className={`font-semibold ${isPassed ? 'text-slate-800' : 'text-slate-400'}`}>
                          {s.label}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {processingStatus === 'completed' && activeStudyId && (
                  <button
                    type="button"
                    onClick={() => onStudyReady(activeStudyId)}
                    className="mt-4 inline-flex items-center space-x-2 space-x-reverse px-6 py-2.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-600/30 transition-all hover:scale-105"
                  >
                    <span>ورود به میز کار تحلیل بالینی</span>
                    <ArrowLeft className="w-4 h-4" />
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
