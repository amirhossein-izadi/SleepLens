import React from 'react';
import { Moon, Database, PlusCircle, ArrowRight } from 'lucide-react';

interface HeaderProps {
  currentView: 'dashboard' | 'upload' | 'workstation';
  onNavigate: (view: 'dashboard' | 'upload') => void;
  activePatientName?: string;
  activeSqiScore?: number | null;
}

export const Header: React.FC<HeaderProps> = ({
  currentView,
  onNavigate,
  activePatientName,
  activeSqiScore,
}) => {
  return (
    <header className="sticky top-0 z-30 bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo & Brand (Right side in RTL) */}
          <div className="flex items-center space-x-3 space-x-reverse cursor-pointer" onClick={() => onNavigate('dashboard')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-600 to-sky-400 flex items-center justify-center shadow-md shadow-brand-500/20 text-white">
              <Moon className="w-5 h-5 fill-current" />
            </div>
            <div>
              <div className="flex items-center space-x-2 space-x-reverse">
                <span className="text-xl font-bold tracking-tight text-slate-900">اسلیپ‌لنز (SleepLens)</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-200">
                  هوش مصنوعی بالینی
                </span>
              </div>
              <p className="text-xs text-slate-500 font-medium">سامانه‌ی تصمیم‌یار بالینی متخصصان طب خواب</p>
            </div>
          </div>

          {/* Center Context (When in Workstation) */}
          {currentView === 'workstation' && activePatientName && (
            <div className="hidden md:flex items-center space-x-3 space-x-reverse px-4 py-1.5 rounded-lg bg-slate-100 border border-slate-200">
              <span className="text-xs font-medium text-slate-500">بیمار فعال:</span>
              <span className="text-sm font-bold text-slate-800">{activePatientName}</span>
              {activeSqiScore !== null && activeSqiScore !== undefined && (
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                  نمره کیفیت خواب: {activeSqiScore.toFixed(1)}
                </span>
              )}
            </div>
          )}

          {/* Actions & Navigation (Left side in RTL) */}
          <div className="flex items-center space-x-3 space-x-reverse">
            {currentView !== 'dashboard' && (
              <button
                onClick={() => onNavigate('dashboard')}
                className="inline-flex items-center space-x-1.5 space-x-reverse px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              >
                <ArrowRight className="w-4 h-4" />
                <span>داشبورد آزمایش‌ها</span>
              </button>
            )}

            {currentView === 'dashboard' && (
              <button
                onClick={() => onNavigate('upload')}
                className="inline-flex items-center space-x-2 space-x-reverse px-4 py-2 rounded-lg text-sm font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-sm shadow-brand-600/30 transition-all hover:scale-[1.02]"
              >
                <PlusCircle className="w-4 h-4" />
                <span>بارگذاری آزمایش جدید</span>
              </button>
            )}

            <a
              href="http://127.0.0.1:8000/admin/"
              target="_blank"
              rel="noreferrer"
              title="مشاهده پنل دیتابیس جنگو"
              className="inline-flex items-center space-x-1.5 space-x-reverse px-3 py-1.5 rounded-lg text-xs font-medium text-slate-500 hover:text-slate-800 bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-colors"
            >
              <Database className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">پنل دیتابیس</span>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};
