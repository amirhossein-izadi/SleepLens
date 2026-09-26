import React, { useState } from 'react';
import { Header } from './components/layout/Header';
import { StudiesDashboard } from './components/dashboard/StudiesDashboard';
import { UploadWizard } from './components/upload/UploadWizard';
import { StudyWorkstation } from './components/workstation/StudyWorkstation';

export function App() {
  const [currentView, setCurrentView] = useState<'dashboard' | 'upload' | 'workstation'>('dashboard');
  const [selectedStudyId, setSelectedStudyId] = useState<string | null>(null);

  const handleSelectStudy = (studyId: string) => {
    setSelectedStudyId(studyId);
    setCurrentView('workstation');
  };

  const handleStudyReady = (studyId: string) => {
    setSelectedStudyId(studyId);
    setCurrentView('workstation');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans" dir="rtl">
      <Header
        currentView={currentView}
        onNavigate={(view) => {
          if (view === 'dashboard') {
            setSelectedStudyId(null);
          }
          setCurrentView(view);
        }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {currentView === 'dashboard' && (
          <StudiesDashboard
            onSelectStudy={handleSelectStudy}
            onOpenUpload={() => setCurrentView('upload')}
          />
        )}

        {currentView === 'upload' && (
          <UploadWizard
            onCancel={() => setCurrentView('dashboard')}
            onStudyReady={handleStudyReady}
          />
        )}

        {currentView === 'workstation' && selectedStudyId && (
          <StudyWorkstation
            studyId={selectedStudyId}
            onBackToDashboard={() => {
              setSelectedStudyId(null);
              setCurrentView('dashboard');
            }}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400 font-medium">
        <p>سامانه‌ی هوشمند بالینی اسلیپ‌لنز (SleepLens) — دستیار تخصصی تصمیم‌یار پزشکان و متخصصان طب خواب</p>
      </footer>
    </div>
  );
}

export default App;
