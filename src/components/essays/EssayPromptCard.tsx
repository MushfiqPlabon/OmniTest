import { FileText, PenTool, Trash2 } from "@lucide/solid";
import { Show } from "solid-js";
import type { Schemas } from "@/api/client";

interface EssayPromptCardProps {
  prompt: Schemas["PromptResponse"];
  isAdmin: boolean;
  onWrite: (p: Schemas["PromptResponse"]) => void;
  onDelete: (id: number) => void;
}

export function EssayPromptCard(props: EssayPromptCardProps) {
  return (
    <article class="card-hover reading-surface flex flex-col justify-between gap-4 rounded-2xl p-5">
      <div class="space-y-2">
        <div class="flex items-center justify-between gap-2">
          <span class="rounded-full bg-brand/15 px-2.5 py-0.5 text-xs font-medium text-brand">
            {props.prompt.subject}
          </span>
          <span class="text-xs capitalize text-muted tabular-nums">
            {props.prompt.difficulty} · {props.prompt.rubric.max_score} pts
          </span>
        </div>
        <h2 class="flex items-center gap-2 text-base font-semibold text-ink">
          <FileText class="h-4 w-4 shrink-0 text-brand" />
          <span>{props.prompt.topic}</span>
        </h2>
        <p class="line-clamp-3 text-sm text-muted">{props.prompt.prompt_text}</p>
      </div>
      <div class="flex items-center justify-between gap-2 pt-1">
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1.5 rounded-xl bg-brand px-3.5 py-1.5 text-xs font-semibold text-brand-ink"
          onClick={() => props.onWrite(props.prompt)}
        >
          <PenTool class="h-3.5 w-3.5" /> Write response
        </button>
        <Show when={props.isAdmin}>
          <button
            type="button"
            class="rounded-lg p-1.5 text-muted hover:text-danger"
            aria-label={`Delete ${props.prompt.topic}`}
            onClick={() => props.onDelete(props.prompt.id)}
          >
            <Trash2 class="h-4 w-4" />
          </button>
        </Show>
      </div>
    </article>
  );
}
