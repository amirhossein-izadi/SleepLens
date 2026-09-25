"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { FileUp, X } from "lucide-react";
import { useUploadMutation } from "@/lib/api/queries";
import { extractErrorMessage } from "@/lib/errorUtils";
import { Button, InlineLoader, useToasts } from "@/components/ui";
import { cn } from "@/lib/utils";

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

  if (!open) return null;

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
      const study = await uploadMutation.mutateAsync({ file });
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
        className="w-full max-w-lg rounded-2xl bg-card p-6 shadow-soft"
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
            "mt-5 flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors",
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

        <div className="mt-5 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="bright" onClick={handleUpload} disabled={!file || uploadMutation.isPending}>
            {uploadMutation.isPending && <InlineLoader className="text-white" />}
            Upload & analyze
          </Button>
        </div>
      </div>
    </div>
  );
}
