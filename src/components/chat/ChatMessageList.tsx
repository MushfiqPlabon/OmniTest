import autoAnimate from "@formkit/auto-animate";
import { BookOpen, Wrench } from "@lucide/solid";
import { For, Show } from "solid-js";
import type { Schemas } from "@/api/client";
import { MarkdownView } from "@/components/MarkdownView";

export interface DisplayMsg {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  tool_calls?: Schemas["ToolCallRecord"][];
}

export function ChatMessageList(props: { messages: DisplayMsg[]; sending: boolean }) {
  return (
    <div ref={(el) => autoAnimate(el)} class="flex-1 space-y-4 overflow-y-auto pr-1">
      <Show when={props.messages.length === 0}>
        <div class="reading-surface my-8 rounded-2xl p-6 text-center">
          <p class="text-sm font-medium text-ink">Ask a GED or Digital SAT question to get started.</p>
          <p class="mt-1 text-xs text-muted">
            Try: "What is the formula for slope of a line?" or "Generate a 3-question practice quiz on algebra."
          </p>
        </div>
      </Show>

      <For each={props.messages}>
        {(msg) => (
          <div class={["flex", msg.role === "user" ? "justify-end" : "justify-start"]}>
            <div
              class={[
                "max-w-[85%] rounded-2xl px-4 py-3 text-sm",
                msg.role === "user" ? "bg-brand text-brand-ink" : "reading-surface text-ink",
              ]}
            >
              <Show when={msg.role === "assistant"} fallback={<p class="whitespace-pre-wrap">{msg.content}</p>}>
                <MarkdownView content={msg.content} />
              </Show>

              <Show when={msg.sources && msg.sources.length > 0}>
                <div class="mt-2.5 flex flex-wrap gap-1.5 border-t border-edge pt-2">
                  <For each={msg.sources}>
                    {(src) => (
                      <span class="inline-flex items-center gap-1 rounded-full bg-brand/15 px-2.5 py-0.5 text-xs font-medium text-brand">
                        <BookOpen class="h-3 w-3" />
                        {src}
                      </span>
                    )}
                  </For>
                </div>
              </Show>

              <Show when={msg.tool_calls && msg.tool_calls.length > 0}>
                <details class="mt-2 border-t border-edge pt-2 text-xs text-muted">
                  <summary class="inline-flex cursor-pointer items-center gap-1 font-medium text-accent">
                    <Wrench class="h-3 w-3" />
                    Tools used ({msg.tool_calls?.length})
                  </summary>
                  <pre class="mt-1.5 overflow-x-auto rounded-lg bg-canvas p-2 font-mono text-[11px] text-ink">
                    {JSON.stringify(msg.tool_calls, null, 2)}
                  </pre>
                </details>
              </Show>
            </div>
          </div>
        )}
      </For>

      <Show when={props.sending}>
        <div class="reading-surface inline-flex items-center gap-2 rounded-2xl px-4 py-2.5 text-xs text-muted">
          Thinking & checking study guides...
        </div>
      </Show>
    </div>
  );
}
