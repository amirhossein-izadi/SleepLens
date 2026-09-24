import React, { useState } from 'react';
import { 
  Activity, 
  RotateCcw, 
  Edit2, 
  AlertTriangle, 
  CheckCircle2, 
  Sliders, 
  Clock, 
  Layers, 
  Heart, 
  TrendingDown
} from 'lucide-react';
import type { StudyMetricsSummary, MetricDefinition } from '../../types';
import { api } from '../../services/api';

interface MetricsTabProps {
  studyId: string;
  metricsSummary: StudyMetricsSummary | null;
  catalog: MetricDefinition[];
  onMetricsUpdated: (summary: StudyMetricsSummary) => void;
}

export const MetricsTab: React.FC<MetricsTabProps> = ({
  studyId,
  metricsSummary,
  catalog,
  onMetricsUpdated,
}) => {
  const [editingMetric, setEditingMetric] = useState<{ key: string; name: string; val: number; unit: string } | null>(null);
  const [adjustedVal, setAdjustedVal] = useState<number>(0);
  const [rationale, setRationale] = useState<string>('');
  const [saving, setSaving] = useState(false);
  const [recalculating, setRecalculating] = useState(false);

  if (!metricsSummary) {
    return (
      <div className="bg-white rounded-3xl p-12 text-center border border-slate-200">
        <Activity className="w-8 h-8 text-slate-300 animate-spin mx-auto mb-3" />
        <p className="text-sm font-bold text-slate-700">در حال محاسبه متریک‌های پلی‌سومنوگرافی...</p>
      </div>
    );
  }

  const { sqi_score, sqi_category, metrics_data, category_summaries, clinical_alerts, is_manually_adjusted, overrides } = metricsSummary;

  const handleOpenEdit = (key: string, name: string, val: number, unit: string) => {
    setEditingMetric({ key, name, val, unit });
    setAdjustedVal(val);
    setRationale('');
  };

  const handleSaveOverride = async () => {
    if (!editingMetric) return;
    setSaving(true);
    try {
      const updated = await api.overrideMetric(studyId, editingMetric.key, adjustedVal, rationale || 'اصلاح بالینی توسط پزشک معالج');
      onMetricsUpdated(updated);
      setEditingMetric(null);
    } catch (err) {
      alert('خطا در ثبت اصلاحیه متریک: ' + String(err));
    } finally {
      setSaving(false);
    }
  };

  const handleRecalculate = async () => {
    setRecalculating(true);
    try {
      const updated = await api.recalculateMetrics(studyId);
      onMetricsUpdated(updated);
    } catch (err) {
      alert('خطا در محاسبه مجدد: ' + String(err));
    } finally {
      setRecalculating(false);
    }
  };

  const categories = [
    { id: 'continuity', title: 'تداوم خواب (Continuity)', icon: Clock, desc: 'آیا بیمار در طول شب خواب پیوسته داشته است؟' },
    { id: 'fragmentation', title: 'تکه‌تکه‌شدگی خواب (Fragmentation)', icon: TrendingDown, desc: 'خواب شبانه چقدر شکسته و گسسته بوده است؟' },
    { id: 'architecture', title: 'معماری و ساختار مراحل خواب (Architecture)', icon: Layers, desc: 'آیا تناسب خواب عمیق ترمیمی و رؤیا برقرار بوده است؟' },
    { id: 'respiratory', title: 'وقایع تنفسی و ریزساختارها (Respiration)', icon: Heart, desc: 'بررسی وقفه‌های تنفسی (آپنه) و دوک‌های خواب' },
  ];

  let catFa = sqi_category;
  if (sqi_score >= 85) catFa = 'عالی (Optimal)';
  else if (sqi_score >= 75) catFa = 'خوب (Good)';
  else if (sqi_score >= 60) catFa = 'متوسط (Fair)';
  else catFa = 'ضعیف (Poor)';

  return (
    <div className="space-y-6">
      {/* SQI Headline Banner */}
      <div className="bg-gradient-to-l from-slate-950 via-slate-900 to-brand-950 rounded-3xl p-6 text-white shadow-xl flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-5 space-x-reverse">
          <div className="w-20 h-20 rounded-2xl bg-white/10 border border-white/20 backdrop-blur-md flex flex-col items-center justify-center flex-shrink-0">
            <span className="text-3xl font-black tracking-tight">{sqi_score.toFixed(1)}</span>
            <span className="text-[10px] uppercase font-bold text-sky-300">نمره SQI</span>
          </div>
          <div>
            <div className="flex items-center space-x-2.5 space-x-reverse">
              <h3 className="text-xl font-black tracking-tight">شاخص کیفیت خواب (Sleep Quality Index)</h3>
              <span className={`px-3 py-1 rounded-full text-xs font-black ${
                sqi_score >= 85 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                sqi_score >= 75 ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' :
                sqi_score >= 60 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              }`}>
                {catFa}
              </span>
              {is_manually_adjusted && (
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-400 text-slate-950">
                  ★ اصلاحات پزشک اعمال شده
                </span>
              )}
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-xl leading-relaxed">
              شاخص جامع ارزیابی کیفیت خواب شبانه، تلفیق‌کننده کارایی خواب، زمان به خواب رفتن، عمق ترمیمی موج آهسته (N3) و جریمه‌های ناشی از بیداری‌های مکرر.
            </p>
          </div>
        </div>

        <button
          onClick={handleRecalculate}
          disabled={recalculating}
          className="inline-flex items-center space-x-2 space-x-reverse px-5 py-2.5 rounded-xl text-xs font-bold bg-white text-slate-900 hover:bg-slate-100 shadow-md transition-all hover:scale-105 disabled:opacity-50 flex-shrink-0"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${recalculating ? 'animate-spin' : ''}`} />
          <span>{recalculating ? 'در حال محاسبه مجدد...' : 'محاسبه مجدد شاخص SQI'}</span>
        </button>
      </div>

      {/* Clinical Alerts Banner (If Flagged) */}
      {clinical_alerts && clinical_alerts.length > 0 && (
        <div className="bg-amber-50 rounded-3xl p-5 border border-amber-200">
          <div className="flex items-center space-x-2 space-x-reverse text-amber-800 text-xs font-bold uppercase tracking-wider mb-2.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>هشدارهای بالینی شناسایی‌شده ({clinical_alerts.length} مورد)</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-amber-900 font-bold">
            {clinical_alerts.map((alert, idx) => (
              <div key={idx} className="flex items-center space-x-2 space-x-reverse bg-white/80 px-3.5 py-2 rounded-xl border border-amber-200/60">
                <span className="w-2 h-2 rounded-full bg-amber-500 flex-shrink-0" />
                <span>{alert}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 4 Categorized Metric Blocks */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {categories.map((cat) => {
          const summaryData = category_summaries?.[cat.id] || { score: 80, status: 'NORMAL' };
          const categoryDefinitions = catalog.filter((c) => c.category === cat.id);

          return (
            <div key={cat.id} className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
              {/* Category Header */}
              <div className="p-4 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center space-x-3 space-x-reverse">
                  <div className="w-8 h-8 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
                    <cat.icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{cat.title}</h4>
                    <p className="text-[11px] text-slate-500">{cat.desc}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2 space-x-reverse">
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase ${
                    summaryData.status === 'NORMAL' ? 'bg-emerald-100 text-emerald-800' :
                    summaryData.status === 'BORDERLINE' ? 'bg-amber-100 text-amber-800' :
                    'bg-rose-100 text-rose-800'
                  }`}>
                    {summaryData.status === 'NORMAL' ? 'نرمال' : summaryData.status === 'BORDERLINE' ? 'مرزی' : 'غیرطبیعی'}
                  </span>
                  <span className="text-xs font-black text-slate-700">{summaryData.score} <span className="text-[10px] text-slate-400">/ ۱۰۰</span></span>
                </div>
              </div>

              {/* Metric Rows */}
              <div className="p-4 divide-y divide-slate-100 flex-1">
                {categoryDefinitions.map((def) => {
                  const val = metrics_data[def.key];
                  const hasVal = val !== undefined && val !== null;
                  const isOverridden = overrides && def.key in overrides;

                  let isAbnormal = false;
                  if (hasVal) {
                    if (def.normal_min !== null && def.normal_min !== undefined && val < def.normal_min) isAbnormal = true;
                    if (def.normal_max !== null && def.normal_max !== undefined && val > def.normal_max) isAbnormal = true;
                  }

                  return (
                    <div key={def.key} className="py-2.5 flex items-center justify-between group">
                      <div>
                        <div className="flex items-center space-x-1.5 space-x-reverse">
                          <span className="text-xs font-bold text-slate-800">{def.display_name}</span>
                          {isOverridden && (
                            <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                              اصلاح‌شده
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400 mt-0.5">
                          {def.normal_min !== null && def.normal_max !== null
                            ? `محدوده مرجع: ${def.normal_min} تا ${def.normal_max} ${def.unit}`
                            : def.normal_min !== null
                            ? `محدوده مرجع: حداقل ${def.normal_min} ${def.unit}`
                            : def.normal_max !== null
                            ? `محدوده مرجع: حداکثر ${def.normal_max} ${def.unit}`
                            : 'بدون آستانه مشخص'}
                        </p>
                      </div>

                      <div className="flex items-center space-x-3 space-x-reverse">
                        <span className={`text-sm font-black font-mono ${isAbnormal ? 'text-rose-600' : 'text-slate-900'}`}>
                          {hasVal ? `${val} ${def.unit}` : '--'}
                        </span>

                        {def.is_editable && (
                          <button
                            type="button"
                            title="اصلاح دستی مقدار متریک"
                            onClick={() => handleOpenEdit(def.key, def.display_name, val ?? 0, def.unit)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-brand-600 hover:bg-slate-100 transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* METRIC ADJUSTMENT MODAL */}
      {editingMetric && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 space-y-4 text-right">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h4 className="text-sm font-black text-slate-900">اصلاح متریک: {editingMetric.name}</h4>
              <button onClick={() => setEditingMetric(null)} className="text-slate-400 text-xs font-bold">✕</button>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">
                مقدار جدید متریک ({editingMetric.unit})
              </label>
              <input
                type="number"
                step="0.1"
                value={adjustedVal}
                onChange={(e) => setAdjustedVal(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm font-mono font-bold rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-left"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">
                دلیل بالینی اصلاحیه
              </label>
              <input
                type="text"
                placeholder="مثال: فیلتر کردن ۲ آرتیفکت حرکتی در فاز اولیه بیداری"
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-right"
              />
            </div>

            <div className="flex justify-end space-x-2 space-x-reverse pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingMetric(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                انصراف
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={handleSaveOverride}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 text-white hover:bg-brand-700 shadow-md shadow-brand-600/20"
              >
                ذخیره و محاسبه مجدد SQI
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
