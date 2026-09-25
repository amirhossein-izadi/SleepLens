/** Assistant consultation chat (opencode-backed), scoped to one study. */

export type ChatSender = "system" | "user" | "assistant";

export interface AssistantMessage {
  id: string;
  sender: ChatSender;
  content: string;
  created_at: string;
}

/** Shape of GET/POST /studies/{id}/chat/ (docs §4.4). */
export interface AssistantPayload {
  study_id?: string;
  available?: boolean;
  session: {
    id: string;
    title: string;
    context_injected: boolean;
    created_at: string;
    updated_at?: string;
  } | null;
  messages: AssistantMessage[];
}

/** POST /chat/messages/ returns the assistant reply turn (envelope-unwrapped). */
export interface AssistantSendResult {
  reply: AssistantMessage | null;
}
