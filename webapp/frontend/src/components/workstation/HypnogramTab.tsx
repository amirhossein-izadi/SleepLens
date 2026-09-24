import React, { useState } from 'react';
import { 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  Tooltip, 
  CartesianGrid, 
  ReferenceLine 
} from 'recharts';
import { 
  Activity, 
  Edit3, 
  RotateCcw, 
  Check, 
  Info, 
  Sliders, 
  Sparkles,
  Zap
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
  0: 'Wake',
  4: 'REM',
  1: 'N1',
  2: 'N2',
  3: 'N3 (Deep)',
  [-1]: 'Unscored'
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

  // Window view range (for large recordings)
  const [viewRange, setViewRange] = useState<[number, number]>([0, Math.min(epochs.length, 360)]);

  // Format data for Recharts step-line
  const chartData = epochs.slice(viewRange[0], viewRange[1]).map((e) => {
    const hours = Math.floor(e.start_seconds / 3600);
    const mins = Math.floor((e.start_seconds % 3600) / 60);
    const timeLabel = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;

    return {
      index: e.epoch_index,
      time: timeLabel,
      yVal: STAGE_Y_VALUES[e.stage] ?? 0,
      stage: e.stage,
      stageName: STAGE_LABELS[e.stage] || 'Unknown',
      isOverridden: e.is_manually_corrected,
      confidence: (e.confidence * 100).toFixed(0),
      rawEpoch: e,
    };
  });

  // Calculate Stage Architecture summary
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

      // Update local state
      const nextEpochs = epochs.map((e) => (e.epoch_index === updated.epoch_index ? updated : e));
      onEpochsUpdated(nextEpochs);

      // Trigger automatic metrics recalculation
      const recalc = await api.recalculateMetrics(studyId);
      onMetricsUpdated(recalc);

      setSelectedEpoch(null);
    } catch (err) {
      alert('Error updating epoch: ' + String(err));
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
      alert('Error in bulk update: ' + String(err));
    } finally {
      setSavingOverride(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Stage Distribution Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: 'Wake', count: stageCounts.wake, color: 'border-amber-400 text-amber-700 bg-amber-50', norm: '< 10%' },
          { label: 'Stage N1', count: stageCounts.n1, color: 'border-sky-400 text-sky-700 bg-sky-50', norm: '2 - 5%' },
          { label: 'Stage N2', count: stageCounts.n2, color: 'border-blue-500 text-blue-700 bg-blue-50', norm: '45 - 55%' },
          { label: 'Stage N3 (Deep)', count: stageCounts.n3, color: 'border-indigo-600 text-indigo-800 bg-indigo-50', norm: '15 - 25%' },
          { label: 'REM (Dreams)', count: stageCounts.rem, color: 'border-purple-500 text-purple-700 bg-purple-50', norm: '20 - 25%' },
        ].map((s) => {
          const pct = ((s.count / total) * 100).toFixed(1);
          return (
            <div key={s.label} className={`rounded-xl p-3.5 border ${s.color} shadow-sm`}>
              <p className="text-xs font-bold uppercase tracking-wider opacity-80">{s.label}</p>
              <div className="flex items-baseline space-x-2 mt-1">
                <span className="text-2xl font-black">{pct}%</span>
                <span className="text-xs opacity-70">({(s.count * 0.5).toFixed(0)} min)</span>
              </div>
              <p className="text-[11px] opacity-75 mt-1 font-medium">Norm: {s.norm}</p>
            </div>
          );
        })}
      </div>

      {/* Main Hypnogram Chart Canvas */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
              <Activity className="w-4 h-4 text-brand-600" />
              <span>Interactive Polysomnography Hypnogram (AASM 30s Epochs)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Click any point on the timeline to inspect signals or manually correct the sleep stage
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsBulkOpen(true)}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-200 transition-colors"
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Bulk Override</span>
            </button>

            {/* Window selector */}
            {epochs.length > 360 && (
              <div className="flex items-center space-x-1 text-xs text-slate-500 font-medium">
                <span>View:</span>
                <select
                  value={`${viewRange[0]}-${viewRange[1]}`}
                  onChange={(e) => {
                    const [s, end] = e.target.value.split('-').map(Number);
                    setViewRange([s, end]);
                  }}
                  className="px-2 py-1 rounded-md border border-slate-200 bg-slate-50 text-slate-800 text-xs"
                >
                  <option value="0-360">First 3 Hours (Epochs 0-360)</option>
                  <option value="360-720">Middle 3 Hours (Epochs 360-720)</option>
                  <option value={`720-${epochs.length}`}>Final Hours</option>
                  <option value={`0-${epochs.length}`}>Full Night ({epochs.length} epochs)</option>
                </select>
              </div>
            )}
          </div>
        </div>

        {/* Step-line Timeline Chart */}
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={chartData}
              onClick={(e) => {
                if (e && e.activePayload && e.activePayload[0]) {
                  const raw = (e.activePayload[0].payload as { rawEpoch: SleepEpoch }).rawEpoch;
                  handleOpenEdit(raw);
                }
              }}
              margin={{ top: 10, right: 20, left: 0, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              
              <YAxis
                domain={[0, 4]}
                ticks={[0, 1, 2, 3, 4]}
                tickFormatter={(v) => {
                  const map: Record<number, string> = { 4: 'Wake', 3: 'REM', 2: 'N1', 1: 'N2', 0: 'N3' };
                  return map[v] || '';
                }}
                tick={{ fontSize: 11, fontWeight: 600, fill: '#64748b' }}
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
                      <div className="bg-slate-900 text-white rounded-xl p-3 shadow-xl text-xs space-y-1.5 border border-slate-700 min-w-[180px]">
                        <div className="flex justify-between items-center border-b border-slate-700 pb-1">
                          <span className="font-bold">Epoch #{data.index}</span>
                          <span className="text-slate-400">{data.time}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Stage:</span>
                          <span className="font-bold text-sky-400">{data.stageName}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400">Confidence:</span>
                          <span>{data.confidence}%</span>
                        </div>
                        {micro.delta_power_uv2 !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-slate-400">Delta Power:</span>
                            <span>{Number(micro.delta_power_uv2).toFixed(1)} µV²</span>
                          </div>
                        )}
                        {micro.spindles_count !== undefined && (
                          <div className="flex justify-between">
                            <span className="text-slate-400">Spindles:</span>
                            <span>{String(micro.spindles_count)}</span>
                          </div>
                        )}
                        {data.isOverridden && (
                          <div className="text-[10px] text-amber-300 font-semibold pt-1 border-t border-slate-700">
                            ★ Physician Overridden
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
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs font-semibold text-slate-500 pt-3 border-t border-slate-100">
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-400" />
            <span>Wake</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-purple-500" />
            <span>REM</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-sky-400" />
            <span>Stage N1</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-600" />
            <span>Stage N2</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-3 h-3 rounded-full bg-indigo-900" />
            <span>Stage N3 (Deep Sleep)</span>
          </div>
        </div>
      </div>

      {/* SINGLE EPOCH CORRECTION MODAL */}
      {selectedEpoch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div>
                <h4 className="text-base font-bold text-slate-900">
                  Correct Stage for Epoch #{selectedEpoch.epoch_index}
                </h4>
                <p className="text-xs text-slate-400">
                  Time offset: {(selectedEpoch.start_seconds / 60).toFixed(1)} minutes from onset
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
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1">
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Original AI Staging:</span>
                <span className="font-bold text-slate-800">{selectedEpoch.ai_predicted_stage_display}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500 font-medium">Model Certainty:</span>
                <span className="font-bold text-slate-800">{(selectedEpoch.confidence * 100).toFixed(1)}%</span>
              </div>
              {selectedEpoch.metrics && Object.keys(selectedEpoch.metrics).length > 0 && (
                <div className="pt-1.5 border-t border-slate-200 flex flex-wrap gap-2 text-[11px] text-slate-600">
                  {Object.entries(selectedEpoch.metrics).map(([k, v]) => (
                    <span key={k} className="px-1.5 py-0.5 rounded bg-white border border-slate-200">
                      {k}: <b>{typeof v === 'number' ? v.toFixed(1) : String(v)}</b>
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Select Target Stage */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1.5">
                Physician Stage Assignment
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
                    className={`py-2 text-xs font-bold rounded-lg border transition-all ${
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
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-600 mb-1">
                Clinical Rationale / Notes
              </label>
              <input
                type="text"
                placeholder="e.g. Observed sleep spindles (12-14 Hz) and K-complexes"
                value={editReason}
                onChange={(e) => setEditReason(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end space-x-2.5 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedEpoch(null)}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={savingOverride}
                onClick={handleSaveSingleOverride}
                className="inline-flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-sm disabled:opacity-50"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Save Stage & Recalculate SQI</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* BULK OVERRIDE MODAL */}
      {isBulkOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h4 className="text-base font-bold text-slate-900">Bulk Epoch Stage Override</h4>
              <button onClick={() => setIsBulkOpen(false)} className="text-slate-400 p-1 font-bold">✕</button>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-500 mb-1">Start Epoch #</label>
                <input
                  type="number"
                  min={0}
                  max={epochs.length - 1}
                  value={bulkStart}
                  onChange={(e) => setBulkStart(Number(e.target.value))}
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200"
                />
              </div>
              <div>
                <label className="block text-xs font-bold uppercase text-slate-500 mb-1">End Epoch #</label>
                <input
                  type="number"
                  min={0}
                  max={epochs.length - 1}
                  value={bulkEnd}
                  onChange={(e) => setBulkEnd(Number(e.target.value))}
                  className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase text-slate-500 mb-1">Assign Stage</label>
              <select
                value={bulkStage}
                onChange={(e) => setBulkStage(Number(e.target.value))}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200"
              >
                <option value={0}>Wake (0)</option>
                <option value={1}>Stage N1 (1)</option>
                <option value={2}>Stage N2 (2)</option>
                <option value={3}>Stage N3 (Deep Sleep)</option>
                <option value={4}>Stage REM (4)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase text-slate-500 mb-1">Rationale</label>
              <input
                type="text"
                placeholder="Reason for bulk change..."
                value={bulkReason}
                onChange={(e) => setBulkReason(e.target.value)}
                className="w-full px-3 py-1.5 text-xs rounded-lg border border-slate-200"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setIsBulkOpen(false)}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={savingOverride}
                onClick={handleSaveBulkOverride}
                className="px-4 py-1.5 rounded-lg text-xs font-bold bg-brand-600 text-white hover:bg-brand-700"
              >
                Apply Range & Recalculate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
