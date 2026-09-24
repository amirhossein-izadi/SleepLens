import React, { useState } from 'react';
import { 
  Activity, 
  RotateCcw, 
  Check, 
  Sliders, 
  Sparkles,
  Clock
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

const STAGE_COLORS: Record<number, string> = {
  0: '#f59e0b', // Wake - Amber
  4: '#a855f7', // REM - Purple
  1: '#38bdf8', // N1 - Light Sky Blue
  2: '#2563eb', // N2 - Royal Blue
  3: '#312e81', // N3 - Dark Indigo
  [-1]: '#94a3b8',
};

const STAGE_LEVELS: { stage: number; label: string; enLabel: string; y: number; color: string }[] = [
  { stage: 0, label: 'بیداری', enLabel: 'Wake', y: 30, color: '#f59e0b' },
  { stage: 4, label: 'خواب رؤیا', enLabel: 'REM', y: 70, color: '#a855f7' },
  { stage: 1, label: 'مرحله N1', enLabel: 'N1', y: 110, color: '#38bdf8' },
  { stage: 2, label: 'مرحله N2', enLabel: 'N2', y: 150, color: '#2563eb' },
  { stage: 3, label: 'مرحله N3', enLabel: 'N3', y: 190, color: '#312e81' },
];

export const HypnogramTab: React.FC<HypnogramTabProps> = ({
  studyId,
  epochs,
  metricsSummary,
  onEpochsUpdated,
  onMetricsUpdated,
}) => {
  const [selectedEpoch, setSelectedEpoch] = useState<SleepEpoch | null>(null);
  const [hoveredEpoch, setHoveredEpoch] = useState<SleepEpoch | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

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

  const visibleEpochs = epochs.slice(viewRange[0], viewRange[1]);
  const totalVisible = visibleEpochs.length || 1;

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

  // SVG coordinate helpers (Chart spans full width of right column)
  const plotLeft = 10;
  const plotRight = 990;
  const plotWidth = plotRight - plotLeft;
  const getStageY = (stage: number): number => {
    switch (stage) {
      case 0: return 30;  // Wake
      case 4: return 70;  // REM
      case 1: return 110; // N1
      case 2: return 150; // N2
      case 3: return 190; // N3
      default: return 30;
    }
  };

  // Time markers along bottom (every 60 epochs = 30 minutes)
  const timeMarkers: { epochIdx: number; label: string; x: number }[] = [];
  const stepInterval = Math.max(30, Math.floor(totalVisible / 8));
  for (let i = 0; i < totalVisible; i += stepInterval) {
    const epoch = visibleEpochs[i];
    if (epoch) {
      const hours = Math.floor(epoch.start_seconds / 3600);
      const mins = Math.floor((epoch.start_seconds % 3600) / 60);
      const timeLabel = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
      const x = plotLeft + (i / totalVisible) * plotWidth;
      timeMarkers.push({ epochIdx: epoch.epoch_index, label: timeLabel, x });
    }
  }

  return (
    <div className="space-y-6">
      {/* Stage Distribution Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: 'بیداری (Wake)', count: stageCounts.wake, color: 'border-amber-400 text-amber-800 bg-amber-50', dotColor: 'bg-amber-400', norm: 'کمتر از ۱۰٪' },
          { label: 'مرحله N1 (سبک)', count: stageCounts.n1, color: 'border-sky-400 text-sky-800 bg-sky-50', dotColor: 'bg-sky-400', norm: '۲ تا ۵٪' },
          { label: 'مرحله N2 (پایه)', count: stageCounts.n2, color: 'border-blue-500 text-blue-800 bg-blue-50', dotColor: 'bg-blue-600', norm: '۴۵ تا ۵۵٪' },
          { label: 'مرحله N3 (عمیق)', count: stageCounts.n3, color: 'border-indigo-600 text-indigo-900 bg-indigo-50', dotColor: 'bg-indigo-900', norm: '۱۵ تا ۲۵٪' },
          { label: 'خواب REM (رؤیا)', count: stageCounts.rem, color: 'border-purple-500 text-purple-800 bg-purple-50', dotColor: 'bg-purple-500', norm: '۲۰ تا ۲۵٪' },
        ].map((s) => {
          const pct = ((s.count / total) * 100).toFixed(1);
          return (
            <div key={s.label} className={`rounded-2xl p-4 border ${s.color} shadow-sm text-right`}>
              <div className="flex items-center space-x-1.5 space-x-reverse mb-1">
                <span className={`w-2.5 h-2.5 rounded-full ${s.dotColor} flex-shrink-0`} />
                <p className="text-xs font-bold opacity-90">{s.label}</p>
              </div>
              <div className="flex items-baseline space-x-2 space-x-reverse mt-1">
                <span className="text-2xl font-black">{pct}٪</span>
                <span className="text-xs opacity-70 font-bold">({(s.count * 0.5).toFixed(0)} دقیقه)</span>
              </div>
              <p className="text-[11px] opacity-75 mt-1 font-medium">بازه نرمال: {s.norm}</p>
            </div>
          );
        })}
      </div>

      {/* Main Hypnogram Chart Canvas */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 relative">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2 space-x-reverse">
              <Activity className="w-5 h-5 text-brand-600" />
              <span>هیپنوگرام تعاملی پلی‌سومنوگرافی با تفکیک رنگی مراحل استاندارد AASM</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              هر مرحله خواب دارای رنگ تشخیصی اختصاصی است • جهت اصلاح استیج، بر روی هر نقطه از نمودار کلیک نمایید
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

        {/* Multi-Colored Clinical Hypnogram with Dedicated HTML Labels Sidebar */}
        <div 
          className="relative w-full h-80 bg-white rounded-3xl border border-slate-200 overflow-hidden select-none flex items-stretch shadow-sm"
          onMouseLeave={() => setHoveredEpoch(null)}
        >
          {/* 1. Left Column: Pure HTML Stage Labels (100% immune to SVG Bidi bugs!) */}
          <div className="w-56 bg-slate-50/90 border-l border-slate-200 p-4 flex flex-col justify-between select-none text-right flex-shrink-0">
            <div className="text-[11px] font-black uppercase tracking-wider text-slate-400 mb-1 border-b border-slate-200 pb-1">
              مراحل خواب (Stages)
            </div>

            {STAGE_LEVELS.map((lvl) => (
              <div key={lvl.stage} className="flex items-center space-x-2.5 space-x-reverse py-1">
                {/* Stage Color Dot Indicator */}
                <span
                  className="w-3.5 h-3.5 rounded-full flex-shrink-0 shadow-sm border border-white"
                  style={{ backgroundColor: lvl.color }}
                />
                {/* Persian + English label on the exact same row */}
                <div className="flex items-center space-x-1.5 space-x-reverse text-xs font-bold text-slate-800">
                  <span>{lvl.label}</span>
                  <span className="font-mono text-[11px] font-bold text-slate-500">({lvl.enLabel})</span>
                </div>
              </div>
            ))}

            <div className="text-[10px] text-slate-400 pt-1 border-t border-slate-200 text-center font-bold">
              محور زمان (ساعت) ↓
            </div>
          </div>

          {/* 2. Right Column: Pure SVG Chart (Step Lines, Shaded Tints, Transitions) */}
          <div className="flex-1 relative h-full bg-slate-50/30">
            <svg
              viewBox="0 0 1000 230"
              className="w-full h-full"
              preserveAspectRatio="none"
            >
              {/* Horizontal Stage Grid Lines */}
              {STAGE_LEVELS.map((lvl) => (
                <line
                  key={`grid-${lvl.stage}`}
                  x1={plotLeft}
                  y1={lvl.y}
                  x2={plotRight}
                  y2={lvl.y}
                  stroke="#e2e8f0"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
              ))}
            {/* Time Axis Grid Lines */}
            {timeMarkers.map((marker, idx) => (
              <g key={idx}>
                <line
                  x1={marker.x}
                  y1={20}
                  x2={marker.x}
                  y2={205}
                  stroke="#f1f5f9"
                  strokeWidth="1"
                />
                <text
                  x={marker.x}
                  y={220}
                  textAnchor="middle"
                  fontSize="10"
                  fill="#94a3b8"
                  fontFamily="monospace"
                >
                  {marker.label}
                </text>
              </g>
            ))}

            {/* 1. Translucent Shaded Vertical Blocks under Each Stage */}
            {visibleEpochs.map((epoch, idx) => {
              const x1 = plotLeft + (idx / totalVisible) * plotWidth;
              const x2 = plotLeft + ((idx + 1) / totalVisible) * plotWidth;
              const y = getStageY(epoch.stage);
              const color = STAGE_COLORS[epoch.stage] || '#0284c7';
              const width = Math.max(x2 - x1, 1);

              return (
                <rect
                  key={`tint-${epoch.id || idx}`}
                  x={x1}
                  y={y}
                  width={width}
                  height={205 - y}
                  fill={color}
                  opacity={0.18}
                />
              );
            })}

            {/* 2. Vertical Connectors between Different Stages */}
            {visibleEpochs.map((epoch, idx) => {
              if (idx >= totalVisible - 1) return null;
              const nextEpoch = visibleEpochs[idx + 1];
              if (nextEpoch.stage === epoch.stage) return null;

              const x = plotLeft + ((idx + 1) / totalVisible) * plotWidth;
              const y1 = getStageY(epoch.stage);
              const y2 = getStageY(nextEpoch.stage);

              return (
                <line
                  key={`conn-${idx}`}
                  x1={x}
                  y1={y1}
                  x2={x}
                  y2={y2}
                  stroke="#94a3b8"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                />
              );
            })}

            {/* 3. Multi-Colored Horizontal Stepped Line for Each Epoch */}
            {visibleEpochs.map((epoch, idx) => {
              const x1 = plotLeft + (idx / totalVisible) * plotWidth;
              const x2 = plotLeft + ((idx + 1) / totalVisible) * plotWidth;
              const y = getStageY(epoch.stage);
              const color = STAGE_COLORS[epoch.stage] || '#0284c7';

              return (
                <line
                  key={`line-${epoch.id || idx}`}
                  x1={x1}
                  y1={y}
                  x2={x2}
                  y2={y}
                  stroke={color}
                  strokeWidth="4"
                  strokeLinecap="round"
                />
              );
            })}

            {/* 4. Interactive Hit Targets & Hover Lines */}
            {visibleEpochs.map((epoch, idx) => {
              const x1 = plotLeft + (idx / totalVisible) * plotWidth;
              const x2 = plotLeft + ((idx + 1) / totalVisible) * plotWidth;
              const width = Math.max(x2 - x1, 4);

              return (
                <rect
                  key={`hit-${epoch.id || idx}`}
                  x={x1}
                  y={15}
                  width={width}
                  height={195}
                  fill="transparent"
                  className="cursor-pointer hover:fill-brand-500/10"
                  onClick={() => handleOpenEdit(epoch)}
                  onMouseEnter={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    setHoveredEpoch(epoch);
                    setTooltipPos({ x: rect.left, y: rect.top });
                  }}
                />
              );
            })}

            {/* Hover Guide Marker */}
            {hoveredEpoch && (
              <line
                x1={plotLeft + ((hoveredEpoch.epoch_index - viewRange[0]) / totalVisible) * plotWidth}
                y1={15}
                x2={plotLeft + ((hoveredEpoch.epoch_index - viewRange[0]) / totalVisible) * plotWidth}
                y2={205}
                stroke="#0284c7"
                strokeWidth="1.5"
                strokeDasharray="2 2"
              />
            )}
          </svg>

          {/* Floating Tooltip Bubble on Hover */}
          {hoveredEpoch && (
            <div className="absolute top-2 left-4 pointer-events-none bg-slate-900/95 text-white rounded-2xl p-3 shadow-2xl text-xs space-y-1.5 border border-slate-700 min-w-[210px] text-right font-sans backdrop-blur-sm animate-in fade-in duration-150">
              <div className="flex justify-between items-center border-b border-slate-700 pb-1">
                <span className="font-black text-sky-300">اپوک شماره #{hoveredEpoch.epoch_index}</span>
                <span className="text-slate-400 font-mono text-[10px]">
                  {Math.floor(hoveredEpoch.start_seconds / 3600).toString().padStart(2, '0')}:
                  {Math.floor((hoveredEpoch.start_seconds % 3600) / 60).toString().padStart(2, '0')}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400">مرحله خواب:</span>
                <span className="font-bold flex items-center space-x-1.5 space-x-reverse" style={{ color: STAGE_COLORS[hoveredEpoch.stage] }}>
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: STAGE_COLORS[hoveredEpoch.stage] }} />
                  <span>{STAGE_LABELS[hoveredEpoch.stage]}</span>
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">اطمینان مدل AI:</span>
                <span className="font-bold">{(hoveredEpoch.confidence * 100).toFixed(0)}٪</span>
              </div>
              {hoveredEpoch.metrics && (
                <>
                  {hoveredEpoch.metrics.delta_power_uv2 !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">توان دلتا (EEG):</span>
                      <span className="font-bold">{Number(hoveredEpoch.metrics.delta_power_uv2).toFixed(1)} µV²</span>
                    </div>
                  )}
                  {hoveredEpoch.metrics.spindles_count !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">دوک‌های خواب:</span>
                      <span className="font-bold">{String(hoveredEpoch.metrics.spindles_count)}</span>
                    </div>
                  )}
                  {hoveredEpoch.metrics.emg_rms_uv !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-slate-400">تون عضلانی (EMG):</span>
                      <span className="font-bold">{Number(hoveredEpoch.metrics.emg_rms_uv).toFixed(1)} µV</span>
                    </div>
                  )}
                </>
              )}
              {hoveredEpoch.is_manually_corrected && (
                <div className="text-[10px] text-amber-300 font-black pt-1 border-t border-slate-700">
                  ★ اصلاح‌شده توسط پزشک معالج
                </div>
              )}
              <div className="text-[10px] text-sky-400 font-semibold pt-1 text-center">
                جهت اصلاح مرحله کلیک نمایید
              </div>
            </div>
          )}
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

            {/* Select Target Stage with Color Swatches */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-2">
                مرحله خواب تاییدشده توسط پزشک
              </label>
              <div className="grid grid-cols-5 gap-1.5">
                {[
                  { id: 0, label: 'Wake', color: 'border-amber-400 text-amber-900 bg-amber-50' },
                  { id: 1, label: 'N1', color: 'border-sky-400 text-sky-900 bg-sky-50' },
                  { id: 2, label: 'N2', color: 'border-blue-500 text-blue-900 bg-blue-50' },
                  { id: 3, label: 'N3', color: 'border-indigo-600 text-indigo-950 bg-indigo-50' },
                  { id: 4, label: 'REM', color: 'border-purple-500 text-purple-900 bg-purple-50' },
                ].map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => setEditStage(s.id)}
                    className={`py-2 text-xs font-black rounded-xl border transition-all ${
                      editStage === s.id
                        ? 'bg-slate-900 border-slate-900 text-white shadow-md'
                        : `${s.color} hover:opacity-80`
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
