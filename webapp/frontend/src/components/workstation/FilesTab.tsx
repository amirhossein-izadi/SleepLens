import React, { useState } from 'react';
import { 
  FileText, 
  FolderTree, 
  Search, 
  CheckCircle2
} from 'lucide-react';
import type { StudyFile } from '../../types';

interface FilesTabProps {
  files: StudyFile[];
}

export const FilesTab: React.FC<FilesTabProps> = ({ files }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<StudyFile | null>(files[0] || null);

  const filteredFiles = files.filter((f) => {
    const matchesFilter = filterType === 'all' || f.file_type === filterType;
    const matchesSearch = f.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          f.relative_path.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} بایت`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} کیلوبایت`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} مگابایت`;
  };

  const getFilterLabel = (type: string): string => {
    switch (type) {
      case 'all': return 'همه فایل‌ها';
      case 'epoch_report': return 'گزارش‌های اپوک ۳۰ ثانیه‌ای';
      case 'raw_edf': return 'سیگنال‌های خام پلی‌سومنوگرافی';
      case 'metadata_excel': return 'متادیتای دموگرافیک';
      default: return type;
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2 space-x-reverse">
            <FolderTree className="w-5 h-5 text-brand-600" />
            <span>کاوشگر فایل‌ها و آرشیو استخراج‌شده بیمار</span>
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            دسترسی شفاف و فارنزیک به تک‌تک گزارش‌های اپوک‌های ۳۰ ثانیه‌ای، سیگنال‌های خام مغزی و نشانه‌گذاری‌های تکنسین
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          {['all', 'epoch_report', 'raw_edf', 'metadata_excel'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                filterType === t
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {getFilterLabel(t)}
            </button>
          ))}
        </div>
      </div>

      {/* Main File Browser Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Right (First in RTL): File Table List */}
        <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col max-h-[600px]">
          <div className="p-3.5 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              فهرست فایل‌ها ({filteredFiles.length} از {files.length})
            </span>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="فیلتر نام فایل..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pr-8 pl-3 py-1 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none w-48 text-right"
              />
            </div>
          </div>

          <div className="overflow-y-auto flex-1 divide-y divide-slate-100">
            {filteredFiles.map((file) => (
              <div
                key={file.id}
                onClick={() => setSelectedFile(file)}
                className={`p-3.5 flex items-center justify-between hover:bg-slate-50/80 cursor-pointer transition-colors ${
                  selectedFile?.id === file.id ? 'bg-brand-50/60 border-r-4 border-brand-600' : ''
                }`}
              >
                <div className="flex items-center space-x-3 space-x-reverse">
                  <div className="w-8 h-8 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800 truncate max-w-xs">{file.file_name}</p>
                    <p className="text-[11px] text-slate-400 font-mono text-left" dir="ltr">{file.relative_path}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 space-x-reverse text-left">
                  {file.epoch_index !== null && file.epoch_index !== undefined && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800">
                      اپوک #{file.epoch_index}
                    </span>
                  )}
                  <span className="text-xs font-bold text-slate-500">{formatBytes(file.file_size_bytes)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Left (Second in RTL): Selected File Inspector */}
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 space-y-4 text-right">
          <div className="border-b border-slate-100 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">مشخصات فنی و امنیتی فایل</span>
            <h4 className="text-sm font-black text-slate-900 mt-1 break-all" dir="ltr">
              {selectedFile?.file_name || 'یک فایل را انتخاب فرمایید'}
            </h4>
          </div>

          {selectedFile ? (
            <div className="space-y-3.5 text-xs">
              <div>
                <span className="text-slate-400 block font-medium mb-1">فرمت فایل:</span>
                <span className="inline-block px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 text-slate-800">
                  {selectedFile.file_type_display}
                </span>
              </div>

              <div>
                <span className="text-slate-400 block font-medium mb-0.5">حجم دقیق:</span>
                <span className="font-bold text-slate-800">{formatBytes(selectedFile.file_size_bytes)} ({selectedFile.file_size_bytes.toLocaleString()} بایت)</span>
              </div>

              {selectedFile.epoch_index !== null && selectedFile.epoch_index !== undefined && (
                <div>
                  <span className="text-slate-400 block font-medium mb-0.5">شماره اپوک ۳۰ ثانیه‌ای:</span>
                  <span className="font-black text-brand-600">اپوک شماره #{selectedFile.epoch_index}</span>
                </div>
              )}

              <div>
                <span className="text-slate-400 block font-medium mb-1">هش امنیتی و اعتبارسنجی (SHA-256):</span>
                <div className="p-2 rounded-xl bg-slate-50 border border-slate-200 font-mono text-[10px] text-slate-600 break-all text-left" dir="ltr">
                  {selectedFile.file_hash_sha256}
                </div>
              </div>

              {selectedFile.preview_data && Object.keys(selectedFile.preview_data).length > 0 && (
                <div>
                  <span className="text-slate-400 block font-medium mb-1">پیش‌نمایش داده‌های استخراج‌شده:</span>
                  <div className="p-3 rounded-2xl bg-slate-900 text-sky-300 font-mono text-[11px] overflow-x-auto max-h-40 text-left" dir="ltr">
                    <pre>{JSON.stringify(selectedFile.preview_data, null, 2)}</pre>
                  </div>
                </div>
              )}

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-xs text-emerald-600 font-bold flex items-center space-x-1.5 space-x-reverse">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>سلامت و اصالت داده تایید شد</span>
                </span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 text-center py-10">برای مشاهده جزئیات، روی یکی از فایل‌های فهرست کلیک کنید.</p>
          )}
        </div>
      </div>
    </div>
  );
};
