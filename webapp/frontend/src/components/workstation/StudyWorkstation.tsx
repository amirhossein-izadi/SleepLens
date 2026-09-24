import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  BarChart3, 
  FolderTree, 
  FileText, 
  Bot, 
  Loader2, 
  AlertCircle,
  Calendar,
  Clock
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

  const [study, setStudy] = useState<SleepStudy | null>(null);
  const [epochs, setEpochs] = useState<SleepEpoch[]>([]);
  const [metricsSummary, setMetricsSummary] = useState<StudyMetricsSummary | null>(null);
  const [catalog, setCatalog] = useState<MetricDefinition[]>([]);
  const [files, setFiles] = useState<StudyFile[]>([]);
  const [report, setReport] = useState<ClinicalReport | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

      try {
        const reportData = await api.getClinicalReport(studyId);
        setReport(reportData);
      } catch {
        // Report might still be generating
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'بارگذاری میز کار بالینی با خطا مواجه شد');
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
        <h3 className="text-base font-bold text-slate-800">در حال فراخوانی میز کار بالینی...</h3>
        <p className="text-xs text-slate-500 mt-1">بارگذاری اپوک‌های هیپنوگرام، فایل‌های سیگنال و متریک‌های بالینی</p>
      </div>
    );
  }

  if (error || !study) {
    return (
      <div className="max-w-md mx-auto py-20 text-center text-rose-600">
        <AlertCircle className="w-10 h-10 mx-auto mb-3" />
        <h3 className="text-base font-bold">خطا در بارگذاری پرونده</h3>
        <p className="text-xs mt-1 text-slate-600">{error || 'پرونده مورد نظر یافت نشد'}</p>
        <button
          onClick={onBackToDashboard}
          className="mt-4 px-4 py-2 rounded-xl bg-slate-100 text-slate-700 text-xs font-bold hover:bg-slate-200"
        >
          بازگشت به داشبورد پرونده‌ها
        </button>
      </div>
    );
  }

  const patient = study.patient;

  return (
    <div className="space-y-6 pb-20">
      {/* Patient & Study Overview Bar */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4 space-x-reverse">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-sky-500 text-white font-black text-base flex items-center justify-center shadow-md shadow-brand-500/20">
            {patient?.first_name?.[0] || 'ب'}{patient?.last_name?.[0] || 'ت'}
          </div>
          <div>
            <div className="flex items-center space-x-2 space-x-reverse">
              <h2 className="text-lg font-black text-slate-900">
                {patient?.first_name} {patient?.last_name}
              </h2>
              <span className="font-mono text-xs font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                پرونده: {patient?.mrn}
              </span>
            </div>
            <div className="flex items-center space-x-4 space-x-reverse text-xs text-slate-500 mt-1 font-medium">
              <span>{patient?.biological_sex === 'female' ? 'زن' : 'مرد'}</span>
              <span>•</span>
              <span className="flex items-center space-x-1 space-x-reverse">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                <span>تاریخ تست: {study.study_date}</span>
              </span>
              <span>•</span>
              <span className="flex items-center space-x-1 space-x-reverse">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{study.duration_minutes} دقیقه ({study.total_epochs} اپوک ۳۰ ثانیه‌ای)</span>
              </span>
            </div>
          </div>
        </div>

        {/* Quick SQI Badge & Chat Trigger */}
        <div className="flex items-center space-x-3 space-x-reverse">
          {metricsSummary && (
            <div className="flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-2xl bg-slate-50 border border-slate-200">
              <span className="text-[11px] font-bold text-slate-400">شاخص SQI:</span>
              <span className="text-base font-black text-slate-900">{metricsSummary.sqi_score.toFixed(1)}</span>
              <span className="text-xs font-bold text-brand-600">({metricsSummary.sqi_category})</span>
            </div>
          )}

          <button
            onClick={() => setIsChatOpen(true)}
            className="inline-flex items-center space-x-2 space-x-reverse px-5 py-2.5 rounded-2xl text-xs font-bold bg-slate-900 hover:bg-slate-800 text-white shadow-md transition-all hover:scale-105"
          >
            <Bot className="w-4 h-4 text-sky-400" />
            <span>مشاوره هوشمند بالینی</span>
          </button>
        </div>
      </div>

      {/* 4 Workstation Navigation Tabs */}
      <div className="border-b border-slate-200 flex space-x-6 space-x-reverse text-sm font-bold">
        {[
          { id: 'hypnogram', label: '۱. هیپنوگرام و تعیین مراحل خواب', icon: Activity, badge: `${epochs.length} اپوک` },
          { id: 'metrics', label: '۲. شاخص SQI و متریک‌های بالینی', icon: BarChart3, badge: metricsSummary ? `${metricsSummary.sqi_score.toFixed(0)} SQI` : null },
          { id: 'files', label: '۳. فایل‌های استخراج‌شده آرشیو', icon: FolderTree, badge: `${files.length} فایل` },
          { id: 'report', label: '۴. گزارش تشخیصی هوش مصنوعی', icon: FileText, badge: report?.is_signed_off ? 'تاییدشده' : 'پیش‌نویس' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as typeof activeTab)}
            className={`pb-3.5 inline-flex items-center space-x-2 space-x-reverse transition-all border-b-2 ${
              activeTab === tab.id
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            <span>{tab.label}</span>
            {tab.badge && (
              <span className={`px-2 py-0.5 rounded-full text-[10px] font-black ${
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

      {/* Floating Action Button */}
      {!isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          className="fixed bottom-6 right-6 z-40 inline-flex items-center space-x-2.5 space-x-reverse px-5 py-3.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white shadow-2xl shadow-slate-900/40 transition-all hover:scale-105 border border-slate-700 font-bold text-xs"
        >
          <Bot className="w-5 h-5 text-sky-400" />
          <span>مشاوره هوشمند با AI طب خواب</span>
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
