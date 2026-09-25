"use client";

/**
 * AssistantChat
 * Expert consultation with the opencode-backed assistant, grounded in this
 * study's data. The backend persists the session and both message turns.
 */

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Bot, MessageSquare, RotateCcw, Send, Sparkles, User } from "lucide-react";
import {
  useAssistantPromptsQuery,
  useAssistantQuery,
  useAssistantResetMutation,
  useAssistantSendMutation,
} from "@/lib/api/queries";
import type { AssistantMessage } from "@/lib/api";
import { extractErrorMessage } from "@/lib/errorUtils";
import { Button, InlineLoader } from "@/components/ui";
import { useToasts } from "@/components/ui/toast";
import { cn } from "@/lib/utils";

interface AssistantChatProps {
  studyId: string;
  /** Only show the chat once the analysis is complete. */
  enabled: boolean;
  className?: string;
}

export function AssistantChat({ studyId, enabled, className }: AssistantChatProps) {
  const assistantQuery = useAssistantQuery(studyId, enabled);
  const promptsQuery = useAssistantPromptsQuery(studyId, enabled);
  const sendMutation = useAssistantSendMutation(studyId);
  const resetMutation = useAssistantResetMutation(studyId);
  const { error: toastError, success } = useToasts();

  const [draft, setDraft] = useState("");
  const [pendingUser, setPendingUser] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const messages = assistantQuery.data?.messages ?? [];
  const prompts = promptsQuery.data ?? [];

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, pendingUser, sendMutation.isPending]);

  async function send(content: string) {
    const trimmed = content.trim();
    if (!trimmed || sendMutation.isPending) return;
    setDraft("");
    setPendingUser(trimmed);
    try {
      await sendMutation.mutateAsync(trimmed);
    } catch (err) {
      toastError("Assistant unavailable", extractErrorMessage(err, "Could not reach the assistant."));
    } finally {
      setPendingUser(null);
    }
  }

  async function handleReset() {
    try {
      await resetMutation.mutateAsync();
      success("Consultation reset", "The next message starts a fresh opencode session.");
    } catch (err) {
      toastError("Reset failed", extractErrorMessage(err, "Could not reset the consultation."));
    }
  }

  if (!enabled) return null;

  const errorMessage = extractErrorMessage(assistantQuery.error, "");
  const opencodeDown = assistantQuery.isError && /opencode/i.test(errorMessage);

  return (
    <div className={cn("rounded-xl border bg-card shadow-soft", className)}>
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b px-6 py-4">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-light">
            <Bot className="h-5 w-5 text-brand-bright" />
          </span>
          <div>
            <h3 className="flex items-center gap-2 font-semibold">
              SleepLens Assistant
              <span className="rounded-full bg-brand-light px-2 py-0.5 text-[10px] font-medium text-brand">
                opencode
              </span>
            </h3>
            <p className="text-xs text-muted-foreground">
              {assistantQuery.data?.session
                ? "Grounded in this night's case context — continue the consultation."
                : "Grounded in this night's metrics — the first message opens the consultation."}
            </p>
          </div>
        </div>
        {assistantQuery.data?.session && (
          <Button variant="outline" size="sm" onClick={handleReset} loading={resetMutation.isPending}>
            <RotateCcw className="h-3.5 w-3.5" /> New consultation
          </Button>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="max-h-96 min-h-40 space-y-3 overflow-y-auto px-6 py-4">
        {assistantQuery.isLoading ? (
          <div className="flex justify-center py-8">
            <InlineLoader />
          </div>
        ) : opencodeDown ? (
          <div className="rounded-lg border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
            <p className="font-medium text-foreground">Assistant unavailable</p>
            <p className="mt-1">{errorMessage || "The opencode server is not running."}</p>
          </div>
        ) : messages.length === 0 && !pendingUser ? (
          <div className="flex h-28 items-center justify-center text-sm text-muted-foreground">
            Ask anything about this night — the assistant already knows the case data.
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {pendingUser && (
              <MessageBubble
                message={{
                  id: "pending-user",
                  sender: "user",
                  content: pendingUser,
                  created_at: new Date().toISOString(),
                }}
              />
            )}
          </>
        )}
        {sendMutation.isPending && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <InlineLoader /> thinking…
          </div>
        )}
      </div>

      {/* Suggested prompts (only before the first exchange) */}
      {messages.length === 0 && prompts.length > 0 && (
        <div className="flex flex-wrap gap-2 px-6 pb-3">
          {prompts.map((prompt) => (
            <button
              key={prompt}
              onClick={() => send(prompt)}
              className="flex items-center gap-1.5 rounded-full border border-brand-bright/30 bg-brand-bright/5 px-3 py-1.5 text-xs text-brand transition-colors hover:bg-brand-light"
            >
              <Sparkles className="h-3 w-3" />
              {prompt}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form
        className="flex items-end gap-2 border-t px-6 py-4"
        onSubmit={(event) => {
          event.preventDefault();
          send(draft);
        }}
      >
        <textarea
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              send(draft);
            }
          }}
          placeholder="Ask about this night's findings…"
          rows={1}
          className="max-h-32 min-h-10 flex-1 resize-none rounded-lg border border-input bg-card px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
        <Button type="submit" variant="bright" disabled={!draft.trim()} loading={sendMutation.isPending}>
          {!sendMutation.isPending && <Send className="h-4 w-4" />}
          Send
        </Button>
      </form>
    </div>
  );
}


function MessageBubble({ message }: { message: AssistantMessage }) {
  const isUser = message.sender === "user";

  if (message.sender === "system") {
    return (
      <details className="rounded-lg bg-muted/50 px-4 py-3 text-xs text-muted-foreground">
        <summary className="flex cursor-pointer items-center gap-2 font-medium text-foreground/70">
          <MessageSquare className="h-3.5 w-3.5 shrink-0" />
          Injected case context
          <span className="text-[10px] font-normal opacity-60">
            (what the assistant knows — click to open)
          </span>
        </summary>
        <p className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap leading-relaxed opacity-70">
          {message.content}
        </p>
      </details>
    );
  }

  return (
    <div className={cn("flex items-start gap-2.5", isUser && "flex-row-reverse")}>
      <span
        className={cn(
          "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          isUser ? "bg-brand text-primary-foreground" : "bg-brand-light"
        )}
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5 text-brand-bright" />}
      </span>
      <div
        className={cn(
          "max-w-[85%] space-y-1 rounded-xl px-4 py-3 text-sm",
          isUser ? "rounded-tr-sm bg-primary text-primary-foreground" : "rounded-tl-sm border bg-background"
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="prose-sleeplens">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
