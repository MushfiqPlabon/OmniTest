import { Edit3, Trash2 } from "@lucide/solid";
import { For } from "solid-js";
import type { Schemas } from "@/api/client";

export function AdminPromptsTable(props: {
  items: Schemas["PromptResponse"][];
  onEdit: (p: Schemas["PromptResponse"]) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <div class="reading-surface overflow-x-auto rounded-2xl">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-edge text-xs uppercase tracking-wider text-muted">
          <tr>
            <th class="px-4 py-3 font-semibold">Topic</th>
            <th class="px-4 py-3 font-semibold">Subject / Level</th>
            <th class="px-4 py-3 font-semibold">Max Score</th>
            <th class="px-4 py-3 font-semibold">Prompt Excerpt</th>
            <th class="px-4 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-edge">
          <For
            each={props.items}
            fallback={
              <tr>
                <td colspan="5" class="px-4 py-6 text-center text-xs text-muted">
                  No essay prompts found.
                </td>
              </tr>
            }
          >
            {(p) => (
              <tr class="hover:bg-canvas/50">
                <td class="px-4 py-3 font-medium text-ink">{p.topic}</td>
                <td class="px-4 py-3 text-xs text-muted">
                  {p.subject} · {p.difficulty}
                </td>
                <td class="px-4 py-3 font-mono text-xs text-ink tabular-nums">{p.rubric.max_score} pts</td>
                <td class="max-w-xs truncate px-4 py-3 text-xs text-muted">{p.prompt_text}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center justify-end gap-1">
                    <button
                      type="button"
                      class="rounded-lg p-1.5 text-muted hover:text-ink"
                      aria-label={`Edit ${p.topic}`}
                      onClick={() => props.onEdit(p)}
                    >
                      <Edit3 class="h-3.5 w-3.5" />
                    </button>
                    <button
                      type="button"
                      class="rounded-lg p-1.5 text-muted hover:text-danger"
                      aria-label={`Delete ${p.topic}`}
                      onClick={() => props.onDelete(p.id)}
                    >
                      <Trash2 class="h-3.5 w-3.5" />
                    </button>
                  </div>
                </td>
              </tr>
            )}
          </For>
        </tbody>
      </table>
    </div>
  );
}
