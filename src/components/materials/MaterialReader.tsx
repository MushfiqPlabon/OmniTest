import { ArrowLeft } from "@lucide/solid";
import type { JSX } from "@solidjs/web";
import { Show } from "solid-js";
import type { Schemas } from "@/api/client";
import { MarkdownView } from "@/components/MarkdownView";

interface MaterialReaderProps {
  material: Schemas["MaterialResponse"];
  onBack: () => void;
  actions?: JSX.Element;
}

export function MaterialReader(props: MaterialReaderProps) {
  return (
    <article class="mx-auto max-w-[74ch] space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1.5 rounded-xl border border-edge bg-surface px-3 py-1.5 text-xs font-medium text-ink"
          onClick={() => props.onBack()}
        >
          <ArrowLeft class="h-3.5 w-3.5" /> Back to library
        </button>
        <Show when={props.actions}>{props.actions}</Show>
      </div>

      <div class="reading-surface rounded-2xl p-6 sm:p-8 space-y-5">
        <header class="space-y-2 border-b border-edge pb-4">
          <div class="flex flex-wrap items-center gap-2 text-xs text-muted">
            <span class="rounded-full bg-brand/15 px-2.5 py-0.5 font-medium text-brand">{props.material.subject}</span>
            <span>{props.material.topic}</span>
            <span>· {props.material.difficulty}</span>
            <Show when={props.material.source}>
              <span>· Source: {props.material.source}</span>
            </Show>
          </div>
          <h2 class="text-xl sm:text-2xl font-bold tracking-tight text-ink">{props.material.title}</h2>
        </header>
        <MarkdownView content={props.material.content} />
      </div>
    </article>
  );
}
