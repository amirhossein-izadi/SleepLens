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
  Zap,
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
      <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
        <Activity className="w-8 h-8 text-slate-300 animate-spin mx-auto mb-3" />
        <p className="text-sm font-semibold text-slate-700">Metrics are being calculated...</p>
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
      const updated = await api.overrideMetric(studyId, editingMetric.key, adjustedVal, rationale || 'Physician clinical adjustment');
      onMetricsUpdated(updated);
      setEditingMetric(null);
    } catch (err) {
      alert('Error updating metric: ' + String(err));
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
      alert('Error recalculating metrics: ' + String(err));
    } finally {
      setRecalculating(false);
    }
  };

  // Group metrics by clinical category
  const categories = [
    { id: 'continuity', title: 'Sleep Continuity', icon: Clock, desc: 'Did the patient sleep through the night?' },
    { id: 'fragmentation', title: 'Sleep Fragmentation', icon: TrendingDown, desc: 'How broken was the night?' },
    { id: 'architecture', title: 'Sleep Architecture', icon: Layers, desc: 'Did the patient get the right restorative mix?' },
    { id: 'respiratory', title: 'Respiration & Microstructure', icon: Heart, desc: 'Cardiorespiratory stability & events' },
  ];

  return (
    <div className="space-y-6">
      {/* SQI Headline Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-brand-900 rounded-2xl p-6 text-white shadow-md flex flex-col sm:flex-row items-center justify-between gap-6">
        <div className="flex items-center space-x-5">
          <div className="relative flex items-center justify-center">
            <div className="w-20 h-20 rounded-2xl bg-white/10 border border-white/20 backdrop-blur-md flex flex-col items-center justify-center">
              <span className="text-3xl font-black tracking-tight">{sqi_score.toFixed(1)}</span>
              <span className="text-[10px] uppercase font-bold text-sky-300">SQI Score</span>
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-xl font-bold tracking-tight">Sleep Quality Index</h3>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-black uppercase tracking-wider ${
                sqi_score >= 85 ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                sqi_score >= 75 ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30' :
                sqi_score >= 60 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' :
                'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              }`}>
                {sqi_category}
              </span>
              {is_manually_adjusted && (
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-400 text-slate-950">
                  ★ Overrides Active
                </span>
              )}
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-lg">
              Comprehensive clinical index synthesizing sleep continuity, deep restorative slow-wave activity, stage architecture balance, and micro-fragmentation penalties.
            </p>
          </div>
        </div>

        <button
          onClick={handleRecalculate}
          disabled={recalculating}
          className="inline-flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-white text-slate-900 hover:bg-slate-100 shadow-md transition-all hover:scale-105 disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${recalculating ? 'animate-spin' : ''}`} />
          <span>{recalculating ? 'Recalculating...' : 'Recalculate SQI On-Demand'}</span>
        </button>
      </div>

      {/* Clinical Alerts Banner (If Flagged) */}
      {clinical_alerts && clinical_alerts.length > 0 && (
        <div className="bg-amber-50 rounded-2xl p-4 border border-amber-200">
          <div className="flex items-center space-x-2 text-amber-800 text-xs font-bold uppercase tracking-wider mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>Clinical Warning Flags ({clinical_alerts.length})</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-amber-900 font-medium">
            {clinical_alerts.map((alert, idx) => (
              <div key={idx} className="flex items-center space-x-2 bg-white/70 px-3 py-1.5 rounded-lg border border-amber-200/60">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0" />
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
            <div key={cat.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
              {/* Category Header */}
              <div className="p-4 bg-slate-50/80 border-b border-slate-100 flex items-center justify-between">
                <div className="flex items-center space-x-2.5">
                  <div className="w-8 h-8 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
                    <cat.icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{cat.title}</h4>
                    <p className="text-[11px] text-slate-500">{cat.desc}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase ${
                    summaryData.status === 'NORMAL' ? 'bg-emerald-100 text-emerald-800' :
                    summaryData.status === 'BORDERLINE' ? 'bg-amber-100 text-amber-800' :
                    'bg-rose-100 text-rose-800'
                  }`}>
                    {summaryData.status}
                  </span>
                  <span className="text-xs font-bold text-slate-700">{summaryData.score} <span className="text-[10px] text-slate-400">/ 100</span></span>
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
                        <div className="flex items-center space-x-1.5">
                          <span className="text-xs font-semibold text-slate-800">{def.display_name}</span>
                          {isOverridden && (
                            <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.2 rounded border border-amber-200">
                              Adjusted
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-400">
                          {def.normal_min !== null && def.normal_max !== null
                            ? `Ref: ${def.normal_min} - ${def.normal_max} ${def.unit}`
                            : def.normal_min !== null
                            ? `Ref: >= ${def.normal_min} ${def.unit}`
                            : def.normal_max !== null
                            ? `Ref: <= ${def.normal_max} ${def.unit}`
                            : 'No defined threshold'}
                        </p>
                      </div>

                      <div className="flex items-center space-x-3">
                        <span className={`text-sm font-black ${isAbnormal ? 'text-rose-600' : 'text-slate-900'}`}>
                          {hasVal ? `${val} ${def.unit}` : '--'}
                        </span>

                        {def.is_editable && (
                          <button
                            type="button"
                            title="Manually adjust metric"
                            onClick={() => handleOpenEdit(def.key, def.display_name, val ?? 0, def.unit)}
                            className="p-1 rounded-md text-slate-400 hover:text-brand-600 hover:bg-slate-100 transition-colors opacity-0 group-hover:opacity-100"
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
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 space-y-4">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h4 className="text-sm font-bold text-slate-900">Adjust {editingMetric.name}</h4>
              <button onClick={() => setEditingMetric(null)} className="text-slate-400 text-xs font-bold">✕</button>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase text-slate-500 mb-1">
                New Metric Value ({editingMetric.unit})
              </label>
              <input
                type="number"
                step="0.1"
                value={adjustedVal}
                onChange={(e) => setAdjustedVal(Number(e.target.value))}
                className="w-full px-3 py-2 text-sm font-bold rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase text-slate-500 mb-1">
                Documented Clinical Rationale
              </label>
              <input
                type="text"
                placeholder="e.g. Excluded 2 artifacts during lights-off calibration"
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              />
            </div>

            <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setEditingMetric(null)}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={handleSaveOverride}
                className="px-4 py-1.5 rounded-lg text-xs font-bold bg-brand-600 text-white hover:bg-brand-700 shadow-sm"
              >
                Save & Recalculate SQI
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
