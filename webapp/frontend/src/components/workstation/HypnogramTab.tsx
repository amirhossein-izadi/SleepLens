import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid 
} from 'recharts';
import { 
  Activity, 
  RotateCcw, 
  Check, 
  Sliders, 
  Layers,
  Sparkles
} from 'lucide-react';
import type { SleepEpoch, StudyMetricsSummary } from '../../types';
import { api } from '../../services/api';

interface HypnogramTabProps {
  studyId: string;
  epochs: SleepEpoch[];
  metricsSummary?: StudyMetricsSummary | null;
  onEpochsUpdated: (updatedEpochs: SleepEpoch[]) => void;
  onMetricsUpdated: (summary: StudyMetricsSummary) => void;
}

const STAGE_LABELS: Record<number, string> = {
  0: 'بیداری (Wake)',
  4: 'خواب رؤیا (REM)',
  1: 'مرحله N1 (سبک)',
  2: 'مرحله N2 (پایه)',
  3: 'مرحله N3 (عمیق)',
  [-1]: 'نامشخص / آرتیفکت'
};

const STAGE_Y_VALUES: Record<number, number> = {
  0: 4, // Wake top
  4: 3, // REM
  1: 2, // N1
  2: 1, // N2
  3: 0, // N3 bottom
};

export const HypnogramTab: React.FC<HypnogramTabProps> = ({
  studyId,
  epochs,
  metricsSummary,
  onEpochsUpdated,
  onMetricsUpdated,
}) => {
  const [selectedEpoch, setSelectedEpoch] = useState<SleepEpoch | null>(null);
  const [editStage, setEditStage] = useState<number>(0);
  const [editReason, setEditReason] = useState<string>('');
  const [savingOverride, setSavingOverride] = useState(false);

  // Bulk Edit state
  const [isBulkOpen, setIsBulkOpen] = useState(false);
  const [bulkStart, setBulkStart] = useState(0);
  const [bulkEnd, setBulkEnd] = useState(10);
  const [bulkStage, setBulkStage] = useState(2);
  const [bulkReason, setBulkReason] = useState('');

  // Window view range
  const [viewRange, setViewRange] = useState<[number, number]>([0, Math.min(epochs.length, 360)]);

  const chartData = epochs.slice(viewRange[0], viewRange[1]).map((e) => {
    const hours = Math.floor(e.start_seconds / 3600);
    const mins = Math.floor((e.start_seconds % 3600) / 60);
    const timeLabel = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;

    return {
      index: e.epoch_index,
      time: timeLabel,
      yVal: STAGE_Y_VALUES[e.stage] ?? 0,
      stage: e.stage,
      stageName: STAGE_LABELS[e.stage] || 'نامشخص',
      isOverridden: e.is_manually_corrected,
      confidence: (e.confidence * 100).toFixed(0),
      rawEpoch: e,
    };
  });

  const total = epochs.length || 1;
  const stageCounts = {
    wake: epochs.filter((e) => e.stage === 0).length,
    n1: epochs.filter((e) => e.stage === 1).length,
    n2: epochs.filter((e) => e.stage === 2).length,
    n3: epochs.filter((e) => e.stage === 3).length,
    rem: epochs.filter((e) => e.stage === 4).length,
  };

  const handleOpenEdit = (epoch: SleepEpoch) => {
    setSelectedEpoch(epoch);
    setEditStage(epoch.stage);
    setEditReason(epoch.correction_reason || '');
  };

  const handleSaveSingleOverride = async () => {
    if (!selectedEpoch) return;
    setSavingOverride(true);
    try {
      const updated = await api.overrideEpoch(
        studyId,
        selectedEpoch.epoch_index,
        editStage,
        editReason
      );

      const nextEpochs = epochs.map((e) => (e.epoch_index === updated.epoch_index ? updated : e));
      onEpochsUpdated(nextEpochs);

      const recalc = await api.recalculateMetrics(studyId);
      onMetricsUpdated(recalc);

      setSelectedEpoch(null);
    } catch (err) {
      alert('خطا در اصلاح مرحله اپوک: ' + String(err));
    } finally {
      setSavingOverride(false);
    }
  };

  const handleSaveBulkOverride = async () => {
    setSavingOverride(true);
    try {
      await api.bulkOverrideEpochs(studyId, bulkStart, bulkEnd, bulkStage, bulkReason);
      const refreshed = await api.getStudyHypnogram(studyId);
      onEpochsUpdated(refreshed);

      const recalc = await api.recalculateMetrics(studyId);
      onMetricsUpdated(recalc);

      setIsBulkOpen(false);
    } catch (err) {
      alert('خطا در اصلاح بازه‌ای: ' + String(err));
    } finally {
      setSavingOverride(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Stage Distribution Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: 'بیداری (Wake)', count: stageCounts.wake, color: 'border-amber-400 text-amber-800 bg-amber-50', norm: 'کمتر از ۱۰٪' },
          { label: 'مرحله N1 (سبک)', count: stageCounts.n1, color: 'border-sky-400 text-sky-800 bg-sky-50', norm: '۲ تا ۵٪' },
          { label: 'مرحله N2 (پایه)', count: stageCounts.n2, color: 'border-blue-500 text-blue-800 bg-blue-50', norm: '۴۵ تا ۵۵٪' },
          { label: 'مرحله N3 (عمیق)', count: stageCounts.n3, color: 'border-indigo-600 text-indigo-900 bg-indigo-50', norm: '۱۵ تا ۲۵٪' },
          { label: 'خواب REM (رؤیا)', count: stageCounts.rem, color: 'border-purple-500 text-purple-800 bg-purple-50', norm: '۲۰ تا ۲۵٪' },
        ].map((s) => {
          const pct = ((s.count / total) * 100).toFixed(1);
          return (
            <div key={s.label} className={`rounded-2xl p-4 border ${s.color} shadow-sm text-right`}>
              <p className="text-xs font-bold opacity-80">{s.label}</p>
              <div className="flex items-baseline space-x-2 space-x-reverse mt-1">
                <span className="text-2xl font-black">{pct}٪</span>
                <span className="text-xs opacity-70">({(s.count * 0.5).toFixed(0)} دقیقه)</span>
              </div>
              <p className="text-[11px] opacity-75 mt-1 font-medium">بازه نرمال: {s.norm}</p>
            </div>
          );
        })}
      </div>

      {/* Main Hypnogram Chart Canvas */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2 space-x-reverse">
              <Activity className="w-5 h-5 text-brand-600" />
              <span>هیپنوگرام تعاملی پلی‌سومنوگرافی (اپوک‌های ۳۰ ثانیه‌ای استاندارد AASM)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              جهت بررسی سیگنال یا اصلاح دستی مرحله خواب، بر روی هر نقطه از نمودار کلیک نمایید
            </p>
          </div>

          <div className="flex items-center space-x-2 space-x-reverse">
            <button
              onClick={() => setIsBulkOpen(true)}
              className="inline-flex items-center space-x-1.5 space-x-reverse px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>اصلاح بازه‌ای استیج‌ها</span>
            </button>

            {epochs.length > 360 && (
              <div className="flex items-center space-x-1.5 space-x-reverse text-xs text-slate-500 font-bold">
                <span>بازه نمایش:</span>
                <select
                  value={`${viewRange[0]}-${viewRange[1]}`}
                  onChange={(e) => {
                    const [s, end] = e.target.value.split('-').map(Number);
                    setViewRange([s, end]);
                  }}
                  className="px-2.5 py-1 rounded-lg border border-slate-200 bg-slate-50 text-slate-800 text-xs font-medium"
                >
                  <option value="0-360">۳ ساعت اول (اپوک‌های ۰ تا ۳۶۰)</option>
                  <option value="360-720">۳ ساعت میانی (اپوک‌های ۳۶۰ تا ۷۲۰)</option>
                  <option value={`720-${epochs.length}`}>ساعات پایانی خواب</option>
                  <option value={`0-${epochs.length}`}>کل شب ({epochs.length} اپوک)</option>
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Step-line Timeline Chart */}
        <div className="h-72 w-full" dir="ltr">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              onClick={(e) => {
                if (e && e.activePayload && e.activePayload[0]) {
                  const raw = (e.activePayload[0].payload as { rawEpoch: SleepEpoch }).rawEpoch;
                  handleOpenEdit(raw);
                }
              }}
              margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              
              <YAxis
                domain={[0, 4]}
                ticks={[0, 1, 2, 3, 4]}
                tickFormatter={(v) => {
                  const map: Record<number, string> = { 4: 'Wake', 3: 'REM', 2: 'N1', 1: 'N2', 0: 'N3' };
                  return map[v] || '';
                }}
                tick={{ fontSize: 11, fontWeight: 700, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
                width={50}
              />

              <XAxis
                dataKey="time"
                tick={{ fontSize: 11, fill: '#94a3b8' }}
                axisLine={{ stroke: '#cbd5e1' }}
                tickLine={false}
              />

              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as {
                      index: number;
                      time: string;
                      stageName: string;
                      isOverridden: boolean;
                      confidence: string;
                      rawEpoch: SleepEpoch;
                    };
                    const micro = data.rawEpoch.metrics || {};

                    return (
                      <div className="bg-slate-900 text-white rounded-2xl p-3.5 shadow-xl text-xs space-y-1.5 border border-slate-700 min-w-[200px] text-right font-sans" dir="rtl">
                        <div className="flex justify-between items-center border-b border-slate-700 pb-1.5">
                          <span className="font-bold">اپوک شماره #{data.index}</span>
                          <span className="text-slate-400 font-mono text-[11px]">{data.time}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">مرحله خواب:</span>
                          <span className="font-bold text-sky-400">{data.stageName}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">اطمینان مدل:</span>
                          <span>{data.confidence}٪</span>
                        </div>
                        {micro.delta_power_uv2 !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-slate-400">توان دلتا (EEG):</span>
                            <span>{Number(micro.delta_power_uv2).toFixed(1)} µV²</span>
                          </div>
                        )}
                        {micro.spindles_count !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-slate-400">دوک‌های خواب:</span>
                            <span>{String(micro.spindles_count)}</span>
                          </div>
                        )}
                        {data.isOverridden && (
                          <div className="text-[10px] text-amber-300 font-bold pt-1 border-t border-slate-700">
                            ★ اصلاح‌شده توسط پزشک معالج
                          </div>
                        )}
                      </div>
                    );
                  }
                  return null;
                }}
              />

              <Line
                type="stepAfter"
                dataKey="yVal"
                stroke="#0284c7"
                strokeWidth={2.5}
                dot={false}
                activeDot={{ r: 6, fill: '#0284c7', stroke: '#fff', strokeWidth: 2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-center gap-5 text-xs font-bold text-slate-500 pt-4 border-t border-slate-100">
          <div className="flex items-center space-x-1.5 space-x-reverse">
            <span className="w-3 h-3 rounded-full bg-amber-400" />
            <span>بیداری (Wake)</span>
          </div>
          <div className="flex items-center space-x-1.5 space-x-reverse">
            <span className="w-3 h-3 rounded-full bg-purple-500" />
            <span>خواب رؤیا (REM)</span>
          </div>
          <div className="flex items-center space-x-1.5 space-x-reverse">
            <span className="w-3 h-3 rounded-full bg-sky-400" />
            <span>مرحله N1 (سبک)</span>
          </div>
          <div className="flex items-center space-x-1.5 space-x-reverse">
            <span className="w-3 h-3 rounded-full bg-blue-600" />
            <span>مرحله N2 (پایه)</span>
          </div>
          <div className="flex items-center space-x-1.5 space-x-reverse">
            <span className="w-3 h-3 rounded-full bg-indigo-900" />
            <span>مرحله N3 (خواب عمیق)</span>
          </div>
        </div>
      </div>

      {/* SINGLE EPOCH CORRECTION MODAL */}
      {selectedEpoch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4 text-right">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h4 className="text-base font-black text-slate-900">
                  اصلاح مرحله خواب برای اپوک شماره #{selectedEpoch.epoch_index}
                </h4>
                <p className="text-xs text-slate-400 mt-0.5">
                  زمان سپری‌شده: {(selectedEpoch.start_seconds / 60).toFixed(1)} دقیقه از شروع تست
                </p>
              </div>
              <button
                onClick={() => setSelectedEpoch(null)}
                className="text-slate-400 hover:text-slate-600 p-1 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            {/* AI Prediction Context */}
            <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">پیش‌بینی اولیه مدل AI:</span>
                <span className="font-bold text-slate-800">{selectedEpoch.ai_predicted_stage_display}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">میزان اطمینان مدل:</span>
                <span className="font-bold text-slate-800">{(selectedEpoch.confidence * 100).toFixed(1)}٪</span>
              </div>
              {selectedEpoch.metrics && Object.keys(selectedEpoch.metrics).length > 0 && (
                <div className="pt-2 border-t border-slate-200 flex flex-wrap gap-1.5 text-[11px] text-slate-600">
                  {Object.entries(selectedEpoch.metrics).map(([k, v]) => (
                    <span key={k} className="px-2 py-0.5 rounded-md bg-white border border-slate-200">
                      {k}: <b>{typeof v === 'number' ? v.toFixed(1) : String(v)}</b>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Select Target Stage */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-2">
                مرحله خواب تاییدشده توسط پزشک
              </label>
              <div className="grid grid-cols-5 gap-1.5">
                {[
                  { id: 0, label: 'Wake' },
                  { id: 1, label: 'N1' },
                  { id: 2, label: 'N2' },
                  { id: 3, label: 'N3' },
                  { id: 4, label: 'REM' },
                ].map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setEditStage(s.id)}
                    className={`py-2 text-xs font-bold rounded-xl border transition-all ${
                      editStage === s.id
                        ? 'bg-brand-600 border-brand-600 text-white shadow-sm'
                        : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Clinical Rationale */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                دلیل بالینی اصلاح استیج (اختیاری)
              </label>
              <input
                type="text"
                placeholder="مثال: رویت امواج شارپ ورتکس یا دوک‌های خواب اختصاصی در EEG"
                value={editReason}
                onChange={(e) => setEditReason(e.target.value)}
                className="w-full px-3.5 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-right"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-2.5 space-x-reverse pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedEpoch(null)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                انصراف
              </button>
              <button
                type="button"
                disabled={savingOverride}
                onClick={handleSaveSingleOverride}
                className="inline-flex items-center space-x-1.5 space-x-reverse px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-md shadow-brand-600/20 disabled:opacity-50 transition-all hover:scale-105"
              >
                <Check className="w-3.5 h-3.5" />
                <span>ذخیره مرحله و محاسبه مجدد SQI</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BULK OVERRIDE MODAL */}
      {isBulkOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4 text-right">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h4 className="text-base font-black text-slate-900">اصلاح بازه‌ای مراحل خواب</h4>
              <button onClick={() => setIsBulkOpen(false)} className="text-slate-400 p-1 font-bold">✕</button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">از اپوک شماره</label>
                <input
                  type="number"
                  min={0}
                  max={epochs.length - 1}
                  value={bulkStart}
                  onChange={(e) => setBulkStart(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 font-mono text-left"
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-600 mb-1">تا اپوک شماره</label>
                <input
                  type="number"
                  min={0}
                  max={epochs.length - 1}
                  value={bulkEnd}
                  onChange={(e) => setBulkEnd(Number(e.target.value))}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 font-mono text-left"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">تعیین مرحله جدید</label>
              <select
                value={bulkStage}
                onChange={(e) => setBulkStage(Number(e.target.value))}
                className="w-full px-3 py-2.5 text-xs rounded-xl border border-slate-200 font-bold"
              >
                <option value={0}>بیداری — Wake (0)</option>
                <option value={1}>مرحله N1 (سبک)</option>
                <option value={2}>مرحله N2 (خواب پایه)</option>
                <option value={3}>مرحله N3 (خواب عمیق موج آهسته)</option>
                <option value={4}>مرحله REM (خواب رؤیا)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-600 mb-1">علت تغییر بازه‌ای</label>
              <input
                type="text"
                placeholder="دلیل بالینی..."
                value={bulkReason}
                onChange={(e) => setBulkReason(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 text-right"
              />
            </div>

            <div className="flex justify-end space-x-2 space-x-reverse pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsBulkOpen(false)}
                className="px-4 py-2 rounded-xl text-xs font-bold text-slate-600 hover:bg-slate-100"
              >
                انصراف
              </button>
              <button
                type="button"
                disabled={savingOverride}
                onClick={handleSaveBulkOverride}
                className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-600 text-white hover:bg-brand-700 shadow-md shadow-brand-600/20"
              >
                اعمال بازه و محاسبه مجدد
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
