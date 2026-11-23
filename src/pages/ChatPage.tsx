import { Plus, Send } from "@lucide/solid";
import { createMemo, createSignal, Errored, For, Loading, refresh } from "solid-js";
import { api, unwrap } from "@/api/client";
import { ChatMessageList, type DisplayMsg } from "@/components/chat/ChatMessageList";
import { ErrorBanner } from "@/components/States";
import { useToast } from "@/state/toast";

export function ChatPage() {
  const toast = useToast();
  const [sessionId, setSessionId] = createSignal<number | null>(null);
  const [messages, setMessages] = createSignal<DisplayMsg[]>([]);
  const [draft, setDraft] = createSignal("");
  const [sending, setSending] = createSignal(false);

  const sessions = createMemo(async () => unwrap(api.GET("/api/v1/chat/sessions")));

  const openSession = async (id: number) => {
    try {
      const detail = await unwrap(
        api.GET("/api/v1/chat/sessions/{session_id}", { params: { path: { session_id: id } } }),
      );
      setSessionId(detail.id);
      setMessages(
        (detail.messages ?? []).map((m) => ({
          role: m.role === "user" ? "user" : "assistant",
          content: m.content,
        })),
      );
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Failed to load conversation", "error");
    }
  };

  const sendMessage = async (e?: Event) => {
    e?.preventDefault();
    const text = draft().trim();
    if (!text || sending()) return;
    const priorHistory = messages().map((m) => ({ role: m.role, content: m.content }));
    setDraft("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const res = await unwrap(
        api.POST("/api/v1/chat", { body: { message: text, history: priorHistory, session_id: sessionId() } }),
      );
      setSessionId(res.session_id);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.message, sources: res.sources, tool_calls: res.tool_calls },
      ]);
      void refresh(sessions);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Tutor request failed", "error");
    } finally {
      setSending(false);
    }
  };

  return (
    <div class="grid gap-5 lg:grid-cols-[17rem_1fr]">
      <aside class="reading-surface flex h-fit flex-col gap-3 rounded-2xl p-4 lg:max-h-[75dvh]">
        <div class="flex items-center justify-between">
          <h2 class="text-sm font-semibold text-ink">Saved Sessions</h2>
          <button
            type="button"
            class="glass-btn inline-flex items-center gap-1 rounded-lg bg-brand px-2.5 py-1 text-xs font-medium text-brand-ink"
            onClick={() => {
              setSessionId(null);
              setMessages([]);
            }}
          >
            <Plus class="h-3.5 w-3.5" />
            New
          </button>
        </div>

        <Errored fallback={(err, reset) => <ErrorBanner error={err} onRetry={reset} />}>
          <Loading fallback={<p class="text-xs text-muted">Loading threads...</p>}>
            <div class="flex flex-col gap-1 overflow-y-auto">
              <For each={sessions()} fallback={<p class="text-xs text-muted">No saved sessions yet.</p>}>
                {(s) => (
                  <button
                    type="button"
                    class={[
                      "truncate rounded-xl px-3 py-2 text-left text-xs font-medium transition-colors",
                      sessionId() === s.id ? "bg-brand text-brand-ink" : "text-ink hover:bg-canvas",
                    ]}
                    onClick={() => openSession(s.id)}
                  >
                    {s.title}
                  </button>
                )}
              </For>
            </div>
          </Loading>
        </Errored>
      </aside>

      <section class="glass-surface flex min-h-[72dvh] flex-col rounded-3xl p-4 sm:p-5">
        <div class="mb-3 flex items-center justify-between border-b border-edge pb-3">
          <div>
            <h1 id="page-heading" tabindex="-1" class="text-lg font-bold text-ink">
              AI Tutor Chat
            </h1>
            <p class="text-xs text-muted">Answers cite your curriculum library and generate quizzes on demand.</p>
          </div>
        </div>

        <ChatMessageList messages={messages()} sending={sending()} />

        <form onSubmit={sendMessage} class="mt-4 flex items-end gap-2 border-t border-edge pt-3">
          <textarea
            rows={2}
            value={draft()}
            onInput={(e) => setDraft(e.currentTarget.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void sendMessage();
              }
            }}
            placeholder="Ask OmniTest Tutor (Enter to send, Shift+Enter for new line)..."
            class="min-h-[2.75rem] flex-1 resize-none rounded-2xl border border-edge bg-canvas px-4 py-2.5 text-sm text-ink placeholder:text-muted"
          />
          <button
            type="submit"
            disabled={sending() || !draft().trim()}
            aria-label="Send message"
            class="glass-btn inline-flex h-11 items-center gap-1.5 rounded-2xl bg-brand px-4 text-sm font-semibold text-brand-ink disabled:opacity-45"
          >
            <Send class="h-4 w-4" />
            <span class="hidden sm:inline">Send</span>
          </button>
        </form>
      </section>
    </div>
  );
}
