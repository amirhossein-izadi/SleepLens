import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Bot, 
  Send, 
  X, 
  User, 
  Loader2, 
  Lightbulb,
  Copy,
  Check
} from 'lucide-react';
import type { ChatSession, ChatMessage, SleepStudy } from '../../types';
import { api } from '../../services/api';

interface AssistantDrawerProps {
  study: SleepStudy;
  isOpen: boolean;
  onClose: () => void;
}

export const AssistantDrawer: React.FC<AssistantDrawerProps> = ({
  study,
  isOpen,
  onClose,
}) => {
  const [session, setSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [inputPrompt, setInputPrompt] = useState('');
  const [streamingReply, setStreamingReply] = useState<string | null>(null);
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };
  useEffect(() => {
    if (!isOpen) return;

    setLoading(true);
    api.getOrCreateChatSession(study.id)
      .then(async (sess) => {
        setSession(sess);
        const msgs = await api.getChatMessages(study.id, sess.id);
        setMessages(msgs);

        try {
          const suggestions = await api.getSuggestedPrompts(study.id, sess.id);
          setSuggestedPrompts(suggestions);
        } catch {
          // ignore
        }
      })
      .catch((err) => console.error('Failed to load chat session:', err))
      .finally(() => setLoading(false));
  }, [isOpen, study.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingReply]);

  const handleSendMessage = async (textToSend?: string) => {
    const prompt = (textToSend || inputPrompt).trim();
    if (!prompt || !session || streamingReply !== null) return;

    setInputPrompt('');

    const tempPhysicianMsg: ChatMessage = {
      id: `temp_${Date.now()}`,
      session_id: session.id,
      sender: 'physician',
      content: prompt,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempPhysicianMsg]);
    setStreamingReply('');

    api.streamChatMessage(
      study.id,
      session.id,
      prompt,
      (delta) => {
        setStreamingReply((prev) => (prev || '') + delta);
      },
      () => {
        setStreamingReply((finalText) => {
          if (finalText) {
            const assistantMsg: ChatMessage = {
              id: `asst_${Date.now()}`,
              session_id: session.id,
              sender: 'assistant',
              content: finalText,
              created_at: new Date().toISOString(),
            };
            setMessages((prev) => [...prev, assistantMsg]);
          }
          return null;
        });
      },
      (err) => {
        console.error('SSE Stream error:', err);
        setStreamingReply(null);
      }
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[460px] bg-white border-l border-slate-200 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300 text-right" dir="rtl">
      {/* Drawer Header */}
      <div className="p-4 bg-slate-900 text-white border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-3 space-x-reverse">
          <div className="w-8 h-8 rounded-xl bg-brand-500/20 text-brand-400 border border-brand-500/30 flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center space-x-2 space-x-reverse">
              <span>مشاور هوشمند بالینی طب خواب</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </h3>
            <p className="text-[11px] text-slate-400">
              پرونده: {study.patient?.first_name} {study.patient?.last_name} ({study.sqi_score?.toFixed(1) || '--'} SQI)
            </p>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Suggested Prompt Chips */}
      {suggestedPrompts.length > 0 && (
        <div className="p-3 bg-slate-50 border-b border-slate-100 overflow-x-auto">
          <div className="flex items-center space-x-1.5 space-x-reverse text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
            <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
            <span>پرسش‌های بالینی پیشنهادی</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {suggestedPrompts.map((s, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(s)}
                className="text-right px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:border-brand-500 hover:bg-brand-50 text-[11px] text-slate-700 font-bold transition-all shadow-sm"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages Stream Area */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {loading ? (
          <div className="py-20 text-center">
            <Loader2 className="w-6 h-6 text-brand-600 animate-spin mx-auto mb-2" />
            <p className="text-xs text-slate-500 font-medium">در حال اتصال به نشست مدل زبانی OpenCode...</p>
          </div>
        ) : (
          <>
            {messages.map((m) => {
              if (m.sender === 'system') {
                return (
                  <div key={m.id} className="p-3.5 rounded-2xl bg-slate-100 text-slate-600 text-[11px] border border-slate-200 font-mono text-right leading-relaxed">
                    <pre className="whitespace-pre-wrap font-sans">{m.content}</pre>
                  </div>
                );
              }

              const isPhysician = m.sender === 'physician';

              return (
                <div key={m.id} className={`flex items-start space-x-2.5 space-x-reverse ${isPhysician ? 'justify-start' : 'justify-end'}`}>
                  {isPhysician ? (
                    <div className="w-7 h-7 rounded-xl bg-slate-800 text-white flex items-center justify-center flex-shrink-0 mt-0.5">
                      <User className="w-3.5 h-3.5" />
                    </div>
                  ) : (
                    <div className="w-7 h-7 rounded-xl bg-brand-50 text-brand-600 border border-brand-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Bot className="w-3.5 h-3.5" />
                    </div>
                  )}

                  <div className={`p-3.5 rounded-2xl max-w-[85%] text-xs shadow-sm leading-relaxed text-right ${
                    isPhysician
                      ? 'bg-brand-600 text-white rounded-tr-none font-bold'
                      : 'bg-white border border-slate-200 text-slate-800 rounded-tl-none font-serif'
                  }`}>
                    {!isPhysician && (
                      <div className="flex justify-end border-b border-slate-100 pb-1 mb-1.5">
                        <button
                          onClick={() => handleCopy(m.content, m.id)}
                          className="text-[10px] text-slate-400 hover:text-brand-600 flex items-center space-x-1 space-x-reverse"
                        >
                          {copiedId === m.id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-600" />
                              <span className="text-emerald-600 font-bold">کپی شد</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>کپی متن</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                </div>
              );
            })}

            {/* Live Streaming Token Bubble */}
            {streamingReply !== null && (
              <div className="flex items-start space-x-2.5 space-x-reverse justify-end">
                <div className="w-7 h-7 rounded-xl bg-brand-50 text-brand-600 border border-brand-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5 animate-pulse" />
                </div>
                <div className="p-3.5 rounded-2xl max-w-[85%] text-xs bg-white border border-brand-200 text-slate-800 rounded-tl-none shadow-md font-serif text-right">
                  <ReactMarkdown>{streamingReply || '...'}</ReactMarkdown>
                  <span className="inline-block w-1.5 h-3.5 mr-1 bg-brand-600 animate-pulse align-middle" />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center space-x-2 space-x-reverse"
        >
          <input
            type="text"
            placeholder="سوال خود در رابطه با هیپنوگرام یا متریک‌های بیمار را بپرسید..."
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            disabled={streamingReply !== null}
            className="flex-1 px-4 py-2.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 text-right font-medium"
          />
          <button
            type="submit"
            disabled={!inputPrompt.trim() || streamingReply !== null}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 text-white shadow-sm disabled:opacity-40 transition-all hover:scale-105 flex-shrink-0"
          >
            <Send className="w-4 h-4 rotate-180" />
          </button>
        </form>
      </div>
    </div>
  );
};
