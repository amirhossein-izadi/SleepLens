import React, { useState, useEffect } from 'react';
import { 
  UploadCloud, 
  User, 
  Calendar, 
  FileArchive, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  ArrowRight, 
  Sparkles,
  Layers,
  Activity,
  FileCheck
} from 'lucide-react';
import { api } from '../../services/api';
import type { Patient, StudyStatus } from '../../types';

interface UploadWizardProps {
  onCancel: () => void;
  onStudyReady: (studyId: string) => void;
}

export const UploadWizard: React.FC<UploadWizardProps> = ({ onCancel, onStudyReady }) => {
  const [step, setStep] = useState<'patient' | 'upload' | 'processing'>('patient');
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loadingPatients, setLoadingPatients] = useState(true);

  // Selected or New Patient State
  const [isNewPatient, setIsNewPatient] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [newPatient, setNewPatient] = useState({
    mrn: '',
    first_name: '',
    last_name: '',
    birth_date: '1985-06-15',
    biological_sex: 'male',
    medical_history: 'Complaints of non-restorative sleep, excessive daytime somnolence, loud snoring.',
  });

  // Upload State
  const [studyType, setStudyType] = useState('full_psg');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Processing Stepper State
  const [activeStudyId, setActiveStudyId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<StudyStatus>('uploaded');
  const [statusMessage, setStatusMessage] = useState('Initializing study session...');

  // Fetch patients for dropdown
  useEffect(() => {
    api.getPatients()
      .then((data) => {
        setPatients(data);
        if (data.length > 0) {
          setSelectedPatientId(data[0].id);
        } else {
          setIsNewPatient(true);
        }
      })
      .catch(() => setIsNewPatient(true))
      .finally(() => setLoadingPatients(false));
  }, []);

  // Poll status when in 'processing' step
  useEffect(() => {
    if (step !== 'processing' || !activeStudyId) return;

    const interval = setInterval(async () => {
      try {
        const statusData = await api.getStudyStatus(activeStudyId);
        setProcessingStatus(statusData.status);

        if (statusData.status === 'extracting') {
          setStatusMessage('Extracting ZIP archive & cataloging 30s epoch files...');
        } else if (statusData.status === 'staging') {
          setStatusMessage('Running deep learning staging model on 30s epochs...');
        } else if (statusData.status === 'computing_metrics') {
          setStatusMessage('Calculating 7-category sleep metrics & composite SQI score...');
        } else if (statusData.status === 'generating_report') {
          setStatusMessage('OpenCode LLM drafting clinical diagnostic evaluation...');
        } else if (statusData.status === 'completed') {
          setStatusMessage('Processing complete! Loading analysis workstation...');
          clearInterval(interval);
          setTimeout(() => {
            onStudyReady(activeStudyId);
          }, 1200);
        } else if (statusData.status === 'failed') {
          setError(statusData.error_log || 'Study processing failed.');
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Status poll error:', err);
      }
    }, 800);

    return () => clearInterval(interval);
  }, [step, activeStudyId, onStudyReady]);

  const handlePatientSubmit = async () => {
    setError(null);
    if (isNewPatient) {
      if (!newPatient.first_name || !newPatient.last_name || !newPatient.mrn) {
        setError('Please fill in patient name and MRN.');
        return;
      }
      try {
        const created = await api.createPatient(newPatient);
        setSelectedPatientId(created.id);
        setStep('upload');
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Could not create patient');
      }
    } else {
      if (!selectedPatientId) {
        setError('Please select a patient.');
        return;
      }
      setStep('upload');
    }
  };

  const handleUploadSubmit = async () => {
    setError(null);
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('patient_id', selectedPatientId);
      formData.append('study_type', studyType);
      formData.append('study_date', new Date().toISOString().split('T')[0]);

      if (selectedFile) {
        formData.append('raw_archive', selectedFile);
      }

      const res = await api.uploadStudy(formData);
      setActiveStudyId(res.study_id);
      setProcessingStatus(res.status);
      setStep('processing');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-slate-200 shadow-lg overflow-hidden">
      {/* Wizard Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 p-6 text-white flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center space-x-2">
            <UploadCloud className="w-5 h-5 text-sky-400" />
            <span>New Polysomnography Study</span>
          </h2>
          <p className="text-xs text-slate-300 mt-1">
            Automated archive extraction, AASM epoch staging, SQI metrics, and clinical report
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs font-semibold">
          <span className={`px-2.5 py-1 rounded-md ${step === 'patient' ? 'bg-brand-600 text-white' : 'bg-slate-700 text-slate-400'}`}>1. Patient</span>
          <span className={`px-2.5 py-1 rounded-md ${step === 'upload' ? 'bg-brand-600 text-white' : 'bg-slate-700 text-slate-400'}`}>2. File Upload</span>
          <span className={`px-2.5 py-1 rounded-md ${step === 'processing' ? 'bg-emerald-600 text-white' : 'bg-slate-700 text-slate-400'}`}>3. AI Pipeline</span>
        </div>
      </div>

      <div className="p-6">
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* STEP 1: PATIENT SELECTION */}
        {step === 'patient' && (
          <div className="space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <span className="text-sm font-bold text-slate-800">Assign Patient Record</span>
              <button
                type="button"
                onClick={() => setIsNewPatient(!isNewPatient)}
                className="text-xs font-semibold text-brand-600 hover:text-brand-700 hover:underline"
              >
                {isNewPatient ? '← Choose Existing Patient' : '+ Register New Patient'}
              </button>
            </div>

            {isNewPatient ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">First Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Farhad"
                    value={newPatient.first_name}
                    onChange={(e) => setNewPatient({ ...newPatient, first_name: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Last Name</label>
                  <input
                    type="text"
                    placeholder="e.g. Aslani"
                    value={newPatient.last_name}
                    onChange={(e) => setNewPatient({ ...newPatient, last_name: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Medical Record Number (MRN)</label>
                  <input
                    type="text"
                    placeholder="e.g. MRN-70412"
                    value={newPatient.mrn}
                    onChange={(e) => setNewPatient({ ...newPatient, mrn: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Biological Sex</label>
                  <select
                    value={newPatient.biological_sex}
                    onChange={(e) => setNewPatient({ ...newPatient, biological_sex: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Clinical History & Chief Complaint</label>
                  <textarea
                    rows={2}
                    placeholder="Document suspected apnea, daytime sleepiness, or nocturnal symptoms..."
                    value={newPatient.medical_history}
                    onChange={(e) => setNewPatient({ ...newPatient, medical_history: e.target.value })}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  />
                </div>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Select Registered Patient</label>
                {loadingPatients ? (
                  <div className="p-3 text-sm text-slate-400 flex items-center space-x-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Loading patient records...</span>
                  </div>
                ) : (
                  <select
                    value={selectedPatientId}
                    onChange={(e) => setSelectedPatientId(e.target.value)}
                    className="w-full px-3 py-2.5 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
                  >
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.first_name} {p.last_name} — {p.mrn} ({p.biological_sex})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            )}

            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={onCancel}
                className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:text-slate-900"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handlePatientSubmit}
                className="inline-flex items-center space-x-2 px-5 py-2 rounded-lg text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-all"
              >
                <span>Continue to File Upload</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: FILE UPLOAD */}
        {step === 'upload' && (
          <div className="space-y-5">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Study Recording Environment</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'full_psg', label: 'Full In-Lab PSG' },
                  { id: 'cassette_home', label: 'Home Cassette' },
                  { id: 'telemetry_hospital', label: 'Hospital Telemetry' },
                ].map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setStudyType(t.id)}
                    className={`p-3 rounded-xl border text-xs font-semibold text-center transition-all ${
                      studyType === t.id
                        ? 'border-brand-600 bg-brand-50 text-brand-700 shadow-sm'
                        : 'border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Dropzone */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Upload Patient Archive</label>
              <div className="border-2 border-dashed border-slate-200 hover:border-brand-500 rounded-2xl p-6 text-center transition-all bg-slate-50/50">
                <FileArchive className="w-10 h-10 text-slate-400 mx-auto mb-2" />
                <p className="text-sm font-semibold text-slate-700">
                  {selectedFile ? selectedFile.name : 'Drag & drop patient ZIP archive here'}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Supports ZIP files with 30s epoch reports, .edf, .epf, or signal npz arrays (up to 500 MB)
                </p>
                
                <input
                  type="file"
                  id="archive-upload"
                  accept=".zip,.edf,.epf,.npz"
                  onChange={(e) => {
                    const file = e.target.files?.[0] || null;
                    if (file) {
                      const validExts = ['.zip', '.edf', '.epf', '.npz'];
                      const isExtValid = validExts.some((ext) => file.name.toLowerCase().endsWith(ext));
                      if (!isExtValid) {
                        setError('Invalid file format. Please upload a .zip archive (containing 30s epoch reports) or a .edf/.epf recording.');
                        setSelectedFile(null);
                        return;
                      }
                      setError(null);
                      setSelectedFile(file);
                    }
                  }}
                  className="hidden"
                />
                
                <div className="mt-4 flex items-center justify-center space-x-3">
                  <label
                    htmlFor="archive-upload"
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-sm cursor-pointer"
                  >
                    <span>Browse Local File</span>
                  </label>
                  
                  <span className="text-xs text-slate-400">or</span>
                  
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedFile(null); // Triggers calibrated synthetic dataset
                      handleUploadSubmit();
                    }}
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-50 border border-sky-200 text-brand-700 hover:bg-sky-100 shadow-sm"
                  >
                    <Sparkles className="w-3.5 h-3.5 text-brand-600" />
                    <span>Run Demo 90-Min Recording</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setStep('patient')}
                className="px-4 py-2 rounded-lg text-sm font-semibold text-slate-600 hover:text-slate-900"
              >
                Back
              </button>
              
              <button
                type="button"
                disabled={submitting}
                onClick={handleUploadSubmit}
                className="inline-flex items-center space-x-2 px-6 py-2 rounded-lg text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white shadow-sm disabled:opacity-50 transition-all"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Uploading...</span>
                  </>
                ) : (
                  <>
                    <span>Start Analysis Pipeline</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: REAL-TIME PIPELINE PROGRESS */}
        {step === 'processing' && (
          <div className="py-6 space-y-6 text-center">
            {processingStatus === 'failed' ? (
              <div className="space-y-4">
                <div className="w-16 h-16 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto shadow-md shadow-rose-500/10">
                  <AlertCircle className="w-8 h-8 text-rose-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-rose-900">Pipeline Execution Failed</h3>
                  <p className="text-xs text-slate-500 mt-1">
                    The study could not be processed due to an archive or signal validation error.
                  </p>
                </div>
                <div className="max-w-md mx-auto p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs font-mono text-left break-words">
                  {error || 'Invalid file format: Please ensure you upload a valid .zip archive or .edf recording.'}
                </div>
                <div className="flex items-center justify-center space-x-3 pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setError(null);
                      setStep('upload');
                      setProcessingStatus('uploaded');
                      setSelectedFile(null);
                    }}
                    className="px-5 py-2.5 rounded-xl text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-all"
                  >
                    Select Another File & Retry
                  </button>
                  <button
                    type="button"
                    onClick={onCancel}
                    className="px-4 py-2.5 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    Cancel to Dashboard
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="w-16 h-16 rounded-2xl bg-brand-50 border border-brand-200 text-brand-600 flex items-center justify-center mx-auto shadow-md shadow-brand-500/10">
                  {processingStatus === 'completed' ? (
                    <CheckCircle2 className="w-8 h-8 text-emerald-600 animate-bounce" />
                  ) : (
                    <Loader2 className="w-8 h-8 text-brand-600 animate-spin" />
                  )}
                </div>

                <div>
                  <h3 className="text-lg font-bold text-slate-900 capitalize">
                    {processingStatus === 'completed' ? 'Study Ready for Analysis!' : processingStatus.replace('_', ' ')}
                  </h3>
                  <p className="text-sm font-medium text-slate-500 mt-1 max-w-md mx-auto">
                    {statusMessage}
                  </p>
                </div>

                {/* Stepper Progress Visualizer */}
                <div className="max-w-md mx-auto space-y-3 text-left">
                  {[
                    { label: 'Unpack Archive & Forensics', activeStatus: ['extracting', 'staging', 'computing_metrics', 'generating_report', 'completed'] },
                    { label: 'AASM 5-Class Epoch Staging', activeStatus: ['staging', 'computing_metrics', 'generating_report', 'completed'] },
                    { label: 'SQI & 7-Category Metrics Calculation', activeStatus: ['computing_metrics', 'generating_report', 'completed'] },
                    { label: 'OpenCode LLM Clinical Report Synthesis', activeStatus: ['generating_report', 'completed'] },
                  ].map((s, idx) => {
                    const isPassed = s.activeStatus.includes(processingStatus);
                    const isCurrent = s.activeStatus[0] === processingStatus;

                    return (
                      <div key={idx} className="flex items-center space-x-3 text-xs">
                        {isPassed && !isCurrent ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                        ) : isCurrent ? (
                          <Loader2 className="w-4 h-4 text-brand-600 animate-spin flex-shrink-0" />
                        ) : (
                          <div className="w-4 h-4 rounded-full border border-slate-300 flex-shrink-0" />
                        )}
                        <span className={`font-medium ${isPassed ? 'text-slate-800' : 'text-slate-400'}`}>
                          {s.label}
                        </span>
                      </div>
                    );
                  })}
                </div>

                {processingStatus === 'completed' && activeStudyId && (
                  <button
                    type="button"
                    onClick={() => onStudyReady(activeStudyId)}
                    className="mt-4 inline-flex items-center space-x-2 px-6 py-2.5 rounded-xl text-sm font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-md shadow-emerald-600/30 transition-all hover:scale-105"
                  >
                    <span>Open Workstation Now</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
