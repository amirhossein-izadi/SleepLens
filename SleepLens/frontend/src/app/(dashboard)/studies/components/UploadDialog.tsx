"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileUp, X } from "lucide-react";
import { useUploadMutation } from "@/lib/api/queries";
import { extractErrorMessage } from "@/lib/errorUtils";
import { Button, InlineLoader, useToasts } from "@/components/ui";
import { cn } from "@/lib/utils";

const PSQI_COMPONENTS = [
  { key: "subjective_quality", label: "Subjective sleep quality" },
  { key: "sleep_latency", label: "Sleep latency" },
  { key: "sleep_duration", label: "Sleep duration" },
  { key: "habitual_efficiency", label: "Habitual sleep efficiency" },
  { key: "disturbances", label: "Sleep disturbances" },
  { key: "medication_use", label: "Use of sleeping medication" },
  { key: "daytime_dysfunction", label: "Daytime dysfunction" },
] as const;

type PsqiState = Partial<Record<(typeof PSQI_COMPONENTS)[number]["key"], number>>;

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
}

export function UploadDialog({ open, onClose }: UploadDialogProps) {
  const router = useRouter();
  const { success, error } = useToasts();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadMutation();

  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [psqiOpen, setPsqiOpen] = useState(false);
  const [psqi, setPsqi] = useState<PsqiState>({});

  if (!open) return null;

  const psqiComplete = PSQI_COMPONENTS.every((component) => psqi[component.key] !== undefined);
  const psqiGlobalScore = PSQI_COMPONENTS.reduce(
    (sum, component) => sum + (psqi[component.key] ?? 0),
    0
  );

  const pickFile = (candidate: File | null) => {
    if (!candidate) return;
    if (!/\.(edf|EDF)$/.test(candidate.name)) {
      error("Unsupported file", "Please upload a .EDF recording file.");
      return;
    }
    setFile(candidate);
  };

  async function handleUpload() {
    if (!file) return;
    try {
      const study = await uploadMutation.mutateAsync({
        file,
        psqi: psqiOpen && psqiComplete
          ? Object.fromEntries(PSQI_COMPONENTS.map((component) => [component.key, psqi[component.key]!]))
          : undefined,
      });
      success("Upload started", `${file.name} is being analyzed.`);
      onClose();
      router.push(`/studies/${study.id}`);
    } catch (err) {
      error("Upload failed", extractErrorMessage(err, "Could not upload the recording."));
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-brand-dark/40 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Upload a study"
    >
      <div
        className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-card p-6 shadow-soft"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Upload a study</h2>
            <p className="mt-0.5 text-sm text-muted-foreground">
              Drop a PSG recording in EDF format. Analysis takes 1–3 minutes.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            pickFile(event.dataTransfer.files?.[0] ?? null);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={cn(
            "mt-5 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors",
            dragging ? "border-brand-bright bg-brand-light" : "border-border hover:border-brand-bright/50"
          )}
        >
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-light">
            <FileUp className="h-6 w-6 text-brand-bright" />
          </div>
          {file ? (
            <>
              <p className="text-sm font-medium">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / (1024 * 1024)).toFixed(1)} MB — click to choose another file
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium">Drag & drop your EDF file here</p>
              <p className="text-xs text-muted-foreground">or click to browse</p>
            </>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".edf"
            className="hidden"
            onChange={(event) => pickFile(event.target.files?.[0] ?? null)}
          />
        </div>

        {/* PSQI (all-or-nothing, 7 components × 0–3) */}
        <div className="mt-5 rounded-xl border border-border/70">
          <div className="flex items-center justify-between gap-3 border-b border-border/50 px-4 py-3">
            <div>
              <p className="text-sm font-medium">PSQI questionnaire</p>
              <p className="text-xs text-muted-foreground">
                Optional — Pittsburgh Sleep Quality Index, all 7 components or none.
              </p>
            </div>
            <button
              onClick={() => {
                setPsqiOpen((value) => !value);
                if (psqiOpen) setPsqi({});
              }}
              className={cn(
                "relative h-6 w-11 shrink-0 rounded-full transition-colors",
                psqiOpen ? "bg-brand-bright" : "bg-muted"
              )}
              aria-label="Toggle PSQI input"
            >
              <span
                className={cn(
                  "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all",
                  psqiOpen ? "left-[22px]" : "left-0.5"
                )}
              />
            </button>
          </div>

          {psqiOpen && (
            <div className="space-y-2 px-4 py-3">
              {PSQI_COMPONENTS.map((component) => (
                <div key={component.key} className="flex items-center justify-between gap-3">
                  <span className="text-xs text-muted-foreground">{component.label}</span>
                  <div className="flex gap-1">
                    {[0, 1, 2, 3].map((score) => (
                      <button
                        key={score}
                        onClick={() => setPsqi((current) => ({ ...current, [component.key]: score }))}
                        className={cn(
                          "h-7 w-9 rounded-md border text-xs font-medium transition-colors",
                          psqi[component.key] === score
                            ? "border-brand-bright bg-brand-bright text-white"
                            : "border-border bg-card text-muted-foreground hover:bg-accent"
                        )}
                        aria-label={`${component.label}: ${score}`}
                      >
                        {score}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              <p
                className={cn(
                  "pt-1 text-xs",
                  psqiComplete ? "text-emerald-600" : "text-amber-600"
                )}
              >
                {psqiComplete
                  ? `Complete — global score ${psqiGlobalScore}/21 (higher = worse)`
                  : `Answer all 7 components (${PSQI_COMPONENTS.filter((c) => psqi[c.key] !== undefined).length}/7)`}
              </p>
            </div>
          )}
        </div>

        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="bright"
            onClick={handleUpload}
            disabled={!file || uploadMutation.isPending || (psqiOpen && !psqiComplete)}
          >
            {uploadMutation.isPending && <InlineLoader className="text-white" />}
            Upload & analyze
          </Button>
        </div>
      </div>
    </div>
  );
}
