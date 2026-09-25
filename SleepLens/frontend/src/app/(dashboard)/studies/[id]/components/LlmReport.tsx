"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { FileText, RefreshCw } from "lucide-react";
import { Button, Card, CardContent, CardHeader, CardTitle, InlineLoader } from "@/components/ui";
import { useGenerateReportMutation } from "@/lib/api/queries";
import { useToasts } from "@/components/ui/toast";
import { extractErrorMessage } from "@/lib/errorUtils";
import { formatDateTime } from "@/lib/format";
import type { ReportPayload } from "@/lib/api";

export function LlmReport({
  studyId,
  report,
  className,
}: {
  studyId: string;
  report: ReportPayload | null;
  className?: string;
}) {
  const generateMutation = useGenerateReportMutation(studyId);
  const [markdown, setMarkdown] = useState<string | null>(report?.markdown ?? null);
  const [generatedAt, setGeneratedAt] = useState<string | null>(report?.generated_at ?? null);
  const { success, error } = useToasts();

  async function handleGenerate() {
    try {
      const generated = await generateMutation.mutateAsync();
      setMarkdown(generated.markdown);
      setGeneratedAt(generated.generated_at ?? null);
      success("Report generated", "The AI narrative is ready below.");
    } catch (err) {
      error("Report generation failed", extractErrorMessage(err, "The LLM service may be unavailable."));
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-3">
        <div>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5 text-brand-bright" />
            AI report
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">
            {generatedAt
              ? `Generated ${formatDateTime(generatedAt)} by the LLM from this night's features.`
              : "Generate a readable narrative from this night's features, PSQI and summary."}
          </p>
        </div>
        <Button variant="bright" size="sm" onClick={handleGenerate} loading={generateMutation.isPending}>
          {!generateMutation.isPending && <RefreshCw className="h-4 w-4" />}
          {markdown ? "Regenerate" : "Generate report"}
        </Button>
      </CardHeader>
      <CardContent>
        {generateMutation.isPending && !markdown ? (
          <div className="flex flex-col items-center gap-3 py-10 text-center">
            <InlineLoader className="h-6 w-6" />
            <p className="text-sm text-muted-foreground">
              Writing the report from your night&apos;s metrics — this can take up to a minute.
            </p>
          </div>
        ) : markdown ? (
          <div className="prose-sleeplens max-h-[32rem] overflow-y-auto pr-2 text-sm leading-relaxed">
            <ReactMarkdown>{markdown}</ReactMarkdown>
          </div>
        ) : (
          <p className="rounded-lg border border-dashed px-4 py-8 text-center text-sm text-muted-foreground">
            No report generated yet. Click <strong>Generate report</strong> to have the LLM narrate
            this night&apos;s results.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
