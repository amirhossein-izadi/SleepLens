import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Search, 
  Calendar, 
  Clock, 
  ChevronLeft, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  FileText,
  UserCheck
} from 'lucide-react';
import type { SleepStudy } from '../../types';
import { api } from '../../services/api';

interface StudiesDashboardProps {
  onSelectStudy: (studyId: string) => void;
  onOpenUpload: () => void;
}

export const StudiesDashboard: React.FC<StudiesDashboardProps> = ({
  onSelectStudy,
  onOpenUpload,
}) => {
  const [studies, setStudies] = useState<SleepStudy[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchStudies = async () => {
    try {
      setLoading(true);
      const data = await api.getStudies();
      setStudies(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'بارگذاری پرونده‌های آزمایش با خطا مواجه شد');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudies();
  }, []);

  const filteredStudies = studies.filter((s) => {
    const query = searchQuery.toLowerCase();
    const patientName = `${s.patient?.first_name || ''} ${s.patient?.last_name || ''}`.toLowerCase();
    const mrn = (s.patient?.mrn || '').toLowerCase();
    return patientName.includes(query) || mrn.includes(query);
  });

  const totalStudies = studies.length;
  const completedStudies = studies.filter((s) => s.status === 'completed');
  const validSqi = completedStudies.filter((s) => s.sqi_score !== null && s.sqi_score !== undefined);
  const avgSqi = validSqi.length
    ? (validSqi.reduce((acc, curr) => acc + (curr.sqi_score || 0), 0) / validSqi.length).toFixed(1)
    : '--';

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 ml-1 text-emerald-600" />
            آماده تحلیل بالینی
          </span>
        );
      case 'failed':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-200">
            <AlertCircle className="w-3.5 h-3.5 ml-1 text-rose-600" />
            خطا در پردازش
          </span>
        );
      case 'extracting':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 ml-1 animate-spin text-sky-600" />
            در حال استخراج زیپ
          </span>
        );
      case 'staging':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-200 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 ml-1 animate-spin text-blue-600" />
            در حال تعیین مراحل خواب
          </span>
        );
      case 'computing_metrics':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-indigo-100 text-indigo-800 border border-indigo-200 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 ml-1 animate-spin text-indigo-600" />
            محاسبه متریک‌های SQI
          </span>
        );
      case 'generating_report':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-800 border border-purple-200 animate-pulse">
            <Loader2 className="w-3.5 h-3.5 ml-1 animate-spin text-purple-600" />
            تدوین گزارش هوش مصنوعی
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-800 border border-slate-200">
            بارگذاری‌شده
          </span>
        );
    }
  };

  const getSqiBadge = (score?: number | null, category?: string | null) => {
    if (score === null || score === undefined) {
      return <span className="text-xs text-slate-400 font-medium">در انتظار تحلیل</span>;
    }

    let color = 'bg-slate-100 text-slate-700 border-slate-200';
    let catFa = category || '';
    if (score >= 85) {
      color = 'bg-emerald-50 text-emerald-700 border-emerald-200';
      catFa = 'عالی (Optimal)';
    } else if (score >= 75) {
      color = 'bg-sky-50 text-sky-700 border-sky-200';
      catFa = 'خوب (Good)';
    } else if (score >= 60) {
      color = 'bg-amber-50 text-amber-700 border-amber-200';
      catFa = 'متوسط (Fair)';
    } else {
      color = 'bg-rose-50 text-rose-700 border-rose-200';
      catFa = 'ضعیف (Poor)';
    }

    return (
      <div className="flex items-center space-x-2 space-x-reverse">
        <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-sm font-black border ${color}`}>
          {score.toFixed(1)}
        </span>
        <span className="text-xs font-semibold text-slate-500">
          {catFa}
        </span>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Clinical Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">کل پرونده‌های ثبت‌شده</p>
            <p className="text-3xl font-black text-slate-900 mt-1">{totalStudies}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-brand-600 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">میانگین نمره کیفیت خواب (SQI)</p>
            <p className="text-3xl font-black text-emerald-600 mt-1">{avgSqi} <span className="text-sm font-medium text-slate-400">/ ۱۰۰</span></p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Activity className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-400">پرونده‌های آماده تحلیل</p>
            <p className="text-3xl font-black text-slate-900 mt-1">{completedStudies.length}</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <UserCheck className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Studies Table Header & Search */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-lg font-black text-slate-900">پرونده‌های پلی‌سومنوگرافی بیماران</h2>
            <p className="text-xs text-slate-500 mt-0.5">برای مشاهده هیپنوگرام، اصلاح متریک‌ها و دریافت گزارش هوش مصنوعی، یک پرونده را انتخاب نمایید</p>
          </div>

          <div className="flex items-center space-x-3 space-x-reverse">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute right-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="جستجوی نام بیمار یا شماره پرونده..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pr-9 pl-4 py-2 text-sm rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all w-64"
              />
            </div>
            <button
              onClick={fetchStudies}
              title="بروزرسانی فهرست پرونده‌ها"
              className="p-2 text-slate-400 hover:text-slate-600 rounded-xl hover:bg-slate-100 border border-slate-200 transition-colors"
            >
              <Activity className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Table Content */}
        {loading ? (
          <div className="p-12 text-center">
            <Loader2 className="w-8 h-8 text-brand-600 animate-spin mx-auto mb-3" />
            <p className="text-sm font-medium text-slate-600">در حال بارگذاری پرونده‌های بیماران...</p>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600">
            <AlertCircle className="w-8 h-8 mx-auto mb-2" />
            <p className="font-semibold text-sm">{error}</p>
          </div>
        ) : filteredStudies.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <h3 className="text-sm font-bold text-slate-800">هیچ پرونده آزمایشی یافت نشد</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              فایل زیپ گزارش‌های بیمار را بارگذاری کنید یا یک آزمایش آزمایشی ۹۰ دقیقه‌ای بسازید.
            </p>
            <button
              onClick={onOpenUpload}
              className="mt-4 inline-flex items-center space-x-1.5 space-x-reverse px-5 py-2.5 rounded-xl text-sm font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-all"
            >
              <span>بارگذاری آزمایش جدید</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-right border-collapse">
              <thead>
                <tr className="bg-slate-50/80 text-[11px] font-black uppercase tracking-wider text-slate-400 border-b border-slate-100">
                  <th className="py-3.5 px-5">نام و مشخصات بیمار</th>
                  <th className="py-3.5 px-5">شماره پرونده (MRN)</th>
                  <th className="py-3.5 px-5">تاریخ آزمایش</th>
                  <th className="py-3.5 px-5">مدت زمان / اپوک‌ها</th>
                  <th className="py-3.5 px-5">وضعیت پردازش</th>
                  <th className="py-3.5 px-5">شاخص کیفیت خواب (SQI)</th>
                  <th className="py-3.5 px-5 text-left">عملیات</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {filteredStudies.map((study) => (
                  <tr
                    key={study.id}
                    onClick={() => onSelectStudy(study.id)}
                    className="hover:bg-slate-50/80 cursor-pointer transition-colors group"
                  >
                    <td className="py-3.5 px-5 font-bold text-slate-900 flex items-center space-x-3 space-x-reverse">
                      <div className="w-8 h-8 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center font-black text-xs">
                        {study.patient?.first_name?.[0] || 'ب'}
                      </div>
                      <div>
                        <div>{study.patient?.first_name} {study.patient?.last_name}</div>
                        <div className="text-xs text-slate-400 font-normal">
                          {study.patient?.biological_sex === 'female' ? 'زن' : 'مرد'}
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-5 font-mono text-xs text-slate-600">
                      {study.patient?.mrn || 'N/A'}
                    </td>
                    <td className="py-3.5 px-5 text-slate-600 text-xs">
                      <div className="flex items-center space-x-1.5 space-x-reverse">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span>{study.study_date}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-5 text-slate-600 text-xs">
                      <div className="flex items-center space-x-1 space-x-reverse text-slate-700 font-bold">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{study.duration_minutes ? `${study.duration_minutes} دقیقه` : '--'}</span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        {study.total_epochs ? `${study.total_epochs} اپوک (۳۰ ثانیه‌ای)` : '--'}
                      </div>
                    </td>
                    <td className="py-3.5 px-5">
                      {getStatusBadge(study.status)}
                    </td>
                    <td className="py-3.5 px-5">
                      {getSqiBadge(study.sqi_score, study.sqi_category)}
                    </td>
                    <td className="py-3.5 px-5 text-left">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectStudy(study.id);
                        }}
                        className="inline-flex items-center space-x-1 space-x-reverse px-3 py-1.5 rounded-lg text-xs font-bold text-brand-600 bg-brand-50 hover:bg-brand-100 transition-colors group-hover:scale-105"
                      >
                        <span>تحلیل بالینی</span>
                        <ChevronLeft className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
