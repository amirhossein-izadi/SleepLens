import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Layers, 
  BarChart3, 
  FolderTree, 
  FileText, 
  Bot, 
  ArrowLeft, 
  Loader2, 
  AlertCircle,
  Calendar,
  Clock,
  User
} from 'lucide-react';
import { api } from '../../services/api';
import type { 
  SleepStudy, 
  SleepEpoch, 
  StudyMetricsSummary, 
  MetricDefinition, 
  StudyFile, 
  ClinicalReport 
} from '../../types';
import { HypnogramTab } from './HypnogramTab';
import { MetricsTab } from './MetricsTab';
import { FilesTab } from './FilesTab';
import { ReportTab } from './ReportTab';
import { AssistantDrawer } from './AssistantDrawer';

interface StudyWorkstationProps {
  studyId: string;
  onBackToDashboard: () => void;
}

export const StudyWorkstation: React.FC<StudyWorkstationProps> = ({
  studyId,
  onBackToDashboard,
}) => {
  const [activeTab, setActiveTab] = useState<'hypnogram' | 'metrics' | 'files' | 'report'>('hypnogram');
  const [isChatOpen, setIsChatOpen] = useState(false);

  // Core Data State
  const [study, setStudy] = useState<SleepStudy | null>(null);
  const [epochs, setEpochs] = useState<SleepEpoch[]>([]);
  const [metricsSummary, setMetricsSummary] = useState<StudyMetricsSummary | null>(null);
  const [catalog, setCatalog] = useState<MetricDefinition[]>([]);
  const [files, setFiles] = useState<StudyFile[]>([]);
  const [report, setReport] = useState<ClinicalReport | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initial Load of all study assets
  const loadStudyAssets = async () => {
    try {
      setLoading(true);
      setError(null);

      const [studyData, hypnoData, metricsData, catalogData, filesData] = await Promise.all([
        api.getStudyDetail(studyId),
        api.getStudyHypnogram(studyId).catch(() => []),
        api.getStudyMetrics(studyId).catch(() => null),
        api.getMetricsCatalog().catch(() => []),
        api.getStudyFiles(studyId).catch(() => []),
      ]);

      setStudy(studyData);
      setEpochs(hypnoData);
      setMetricsSummary(metricsData);
      setCatalog(catalogData);
      setFiles(filesData);

      // Attempt loading report
      try {
        const reportData = await api.getClinicalReport(studyId);
        setReport(reportData);
      } catch {
        // Report might still be generating
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load study workstation');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudyAssets();
  }, [studyId]);

  if (loading) {
    return (
      <div className="py-24 text-center">
        <Loader2 className="w-10 h-10 text-brand-600 animate-spin mx-auto mb-3" />
        <h3 className="text-base font-bold text-slate-800">Loading Clinical Workstation...</h3>
        <p className="text-xs text-slate-500 mt-1">Retrieving hypnogram epochs, signal files, and metrics</p>
      </div>
    );
  }

  if (error || !study) {
    return (
      <div className="max-w-md mx-auto py-20 text-center text-rose-600">
        <AlertCircle className="w-10 h-10 mx-auto mb-3" />
        <h3 className="text-base font-bold">Error Loading Study</h3>
        <p className="text-xs mt-1 text-slate-600">{error || 'Study not found'}</p>
        <button
          onClick={onBackToDashboard}
          className="mt-4 px-4 py-2 rounded-lg bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const patient = study.patient;

  return (
    <div className="space-y-6 pb-20">
      {/* Patient & Study Overview Bar */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-sky-500 text-white font-bold text-base flex items-center justify-center shadow-md shadow-brand-500/20">
            {patient?.first_name?.[0] || 'P'}{patient?.last_name?.[0] || 'T'}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-black text-slate-900">
                {patient?.first_name} {patient?.last_name}
              </h2>
              <span className="font-mono text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                MRN: {patient?.mrn}
              </span>
            </div>
            <div className="flex items-center space-x-4 text-xs text-slate-500 mt-1">
              <span className="capitalize">{patient?.biological_sex || 'Unspecified'}</span>
              <span>•</span>
              <span className="flex items-center space-x-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>Study Date: {study.study_date}</span>
              </span>
              <span>•</span>
              <span className="flex items-center space-x-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{study.duration_minutes} min ({study.total_epochs} epochs)</span>
              </span>
            </div>
          </div>
        </div>

        {/* Quick SQI Badge & Chat Trigger */}
        <div className="flex items-center space-x-3">
          {metricsSummary && (
            <div className="flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Night SQI</span>
              <span className="text-base font-black text-slate-900">{metricsSummary.sqi_score.toFixed(1)}</span>
              <span className="text-xs font-semibold capitalize text-brand-600">({metricsSummary.sqi_category})</span>
            </div>
          )}

          <button
            onClick={() => setIsChatOpen(true)}
            className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white shadow-sm transition-all hover:scale-105"
          >
            <Bot className="w-4 h-4 text-sky-400" />
            <span>Consult AI</span>
          </button>
        </div>
      </div>

      {/* 4 Workstation Navigation Tabs */}
      <div className="border-b border-slate-200 flex space-x-6 text-sm font-semibold">
        {[
          { id: 'hypnogram', label: '1. Hypnogram & Staging', icon: Activity, badge: `${epochs.length} Epochs` },
          { id: 'metrics', label: '2. SQI & Dynamic Metrics', icon: BarChart3, badge: metricsSummary ? `${metricsSummary.sqi_score.toFixed(0)} SQI` : null },
          { id: 'files', label: '3. Extracted Archive Files', icon: FolderTree, badge: `${files.length} Files` },
          { id: 'report', label: '4. AI Diagnostic Report', icon: FileText, badge: report?.is_signed_off ? 'Signed' : 'Draft' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`pb-3.5 inline-flex items-center space-x-2 transition-all border-b-2 ${
              activeTab === tab.id
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
            {tab.badge && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                activeTab === tab.id ? 'bg-brand-50 text-brand-700' : 'bg-slate-100 text-slate-500'
              }`}>
                {tab.badge}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Panes */}
      <div>
        {activeTab === 'hypnogram' && (
          <HypnogramTab
            studyId={study.id}
            epochs={epochs}
            metricsSummary={metricsSummary}
            onEpochsUpdated={(next) => setEpochs(next)}
            onMetricsUpdated={(updatedMetrics) => setMetricsSummary(updatedMetrics)}
          />
        )}

        {activeTab === 'metrics' && (
          <MetricsTab
            studyId={study.id}
            metricsSummary={metricsSummary}
            catalog={catalog}
            onMetricsUpdated={(updatedMetrics) => setMetricsSummary(updatedMetrics)}
          />
        )}

        {activeTab === 'files' && (
          <FilesTab files={files} />
        )}

        {activeTab === 'report' && (
          <ReportTab
            studyId={study.id}
            report={report}
            onReportUpdated={(updatedReport) => setReport(updatedReport)}
          />
        )}
      </div>

      {/* Floating Action Button (Always Accessible) */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-6 right-6 z-40 inline-flex items-center space-x-2.5 px-4 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white shadow-xl shadow-slate-900/30 transition-all hover:scale-105 border border-slate-700"
        >
          <Bot className="w-5 h-5 text-sky-400" />
          <span className="text-xs font-bold">Ask AI Somnologist</span>
        </button>
      )}

      {/* Slide-Over Chat Drawer */}
      <AssistantDrawer
        study={study}
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
      />
    </div>
  );
};
