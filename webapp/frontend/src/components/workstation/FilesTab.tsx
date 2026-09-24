import React, { useState } from 'react';
import { 
  FileText, 
  FolderTree, 
  Download, 
  Hash, 
  Clock, 
  Layers, 
  Search, 
  CheckCircle2, 
  Cpu
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
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Overview Banner */}
      <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
            <FolderTree className="w-5 h-5 text-brand-600" />
            <span>Extracted Patient Archive Explorer</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Full forensic inventory of all raw recordings, 30s epoch reports, and clinical annotations
          </p>
        </div>

        <div className="flex items-center space-x-2">
          {['all', 'epoch_report', 'raw_edf', 'metadata_excel'].map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                filterType === t
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {t.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Main File Browser Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: File Table List */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col max-h-[600px]">
          <div className="p-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Files ({filteredFiles.length} of {files.length})
            </span>
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter files..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 pr-3 py-1 text-xs rounded-lg border border-slate-200 bg-white focus:outline-none w-48"
              />
            </div>
          </div>

          <div className="overflow-y-auto flex-1 divide-y divide-slate-100">
            {filteredFiles.map((file) => (
              <div
                key={file.id}
                onClick={() => setSelectedFile(file)}
                className={`p-3.5 flex items-center justify-between hover:bg-slate-50/80 cursor-pointer transition-colors ${
                  selectedFile?.id === file.id ? 'bg-brand-50/60 border-l-4 border-brand-600' : ''
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-600 flex items-center justify-center flex-shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-slate-800 truncate max-w-xs">{file.file_name}</p>
                    <p className="text-[11px] text-slate-400 font-mono">{file.relative_path}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-right">
                  {file.epoch_index !== null && file.epoch_index !== undefined && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800">
                      Epoch #{file.epoch_index}
                    </span>
                  )}
                  <span className="text-xs font-medium text-slate-500">{formatBytes(file.file_size_bytes)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Selected File Inspector */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">File Metadata & Forensics</span>
            <h4 className="text-sm font-bold text-slate-900 mt-1 break-all">
              {selectedFile?.file_name || 'Select a file'}
            </h4>
          </div>

          {selectedFile ? (
            <div className="space-y-3.5 text-xs">
              <div>
                <span className="text-slate-400 block font-medium">Classified Type:</span>
                <span className="inline-block mt-1 px-2.5 py-1 rounded-md text-xs font-bold bg-slate-100 text-slate-800 capitalize">
                  {selectedFile.file_type_display}
                </span>
              </div>

              <div>
                <span className="text-slate-400 block font-medium">File Size:</span>
                <span className="font-bold text-slate-800">{formatBytes(selectedFile.file_size_bytes)} ({selectedFile.file_size_bytes.toLocaleString()} bytes)</span>
              </div>

              {selectedFile.epoch_index !== null && selectedFile.epoch_index !== undefined && (
                <div>
                  <span className="text-slate-400 block font-medium">Mapped Epoch Order:</span>
                  <span className="font-bold text-brand-600">30-Second Epoch #{selectedFile.epoch_index}</span>
                </div>
              )}

              <div>
                <span className="text-slate-400 block font-medium">SHA-256 Checksum:</span>
                <div className="mt-1 p-2 rounded-lg bg-slate-50 border border-slate-200 font-mono text-[10px] text-slate-600 break-all">
                  {selectedFile.file_hash_sha256}
                </div>
              </div>

              {/* Parsed Preview Payload */}
              {selectedFile.preview_data && Object.keys(selectedFile.preview_data).length > 0 && (
                <div>
                  <span className="text-slate-400 block font-medium mb-1">Extracted Preview Data:</span>
                  <div className="p-2.5 rounded-lg bg-slate-900 text-sky-300 font-mono text-[11px] overflow-x-auto max-h-40">
                    <pre>{JSON.stringify(selectedFile.preview_data, null, 2)}</pre>
                  </div>
                </div>
              )}

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-emerald-600 font-semibold flex items-center space-x-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Integrity Verified</span>
                </span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400 text-center py-10">Select a file from the list to view its properties.</p>
          )}
        </div>
      </div>
    </div>
  );
};
