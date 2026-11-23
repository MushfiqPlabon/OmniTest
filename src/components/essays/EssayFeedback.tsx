import { Award, RotateCcw } from "@lucide/solid";
import { createMemo, For, Show } from "solid-js";
import type { Schemas } from "@/api/client";
import { MarkdownView } from "@/components/MarkdownView";

interface EssayFeedbackProps {
  essay: Schemas["EssayResponse"];
  rubric?: Schemas["EssayRubric"];
  onReset?: () => void;
}

export function EssayFeedback(props: EssayFeedbackProps) {
  const pct = () => (props.essay.max_score > 0 ? Math.round((props.essay.score / props.essay.max_score) * 100) : 0);

  const criterionRows = createMemo(() => {
    const scores = props.essay.criteria_scores ?? {};
    const rubricMap = new Map((props.rubric?.criteria ?? []).map((c) => [c.name.toLowerCase(), c]));
    return Object.entries(scores).map(([name, val]) => {
      const def = rubricMap.get(name.toLowerCase());
      const max = def?.max && def.max > 0 ? def.max : null;
      const ratio = max ? Math.min(100, Math.round((val / max) * 100)) : 100;
      return { name, val, max, desc: def?.desc ?? "", ratio };
    });
  });

  return (
    <section class="reading-surface rounded-2xl p-5 sm:p-6 space-y-5" aria-label="Essay grading feedback">
      <div class="glass-surface rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand/15 text-brand">
            <Award class="h-5 w-5" />
          </div>
          <div>
            <p class="text-xs font-medium uppercase tracking-wider text-muted">Graded Score</p>
            <p class="text-2xl font-bold tabular-nums tracking-tight text-ink">
              {props.essay.score}{" "}
              <span class="text-sm font-normal text-muted">
                / {props.essay.max_score} ({pct()}%)
              </span>
            </p>
          </div>
        </div>

        <Show when={props.onReset}>
          <button
            type="button"
            class="glass-btn inline-flex items-center gap-1.5 rounded-xl border border-edge bg-surface px-3 py-1.5 text-xs font-medium text-ink"
            onClick={() => props.onReset?.()}
          >
            <RotateCcw class="h-3.5 w-3.5" />
            Write another
          </button>
        </Show>
      </div>

      <Show when={criterionRows().length > 0}>
        <div class="grid gap-3 sm:grid-cols-2">
          <For each={criterionRows()}>
            {(row) => (
              <div class="rounded-xl border border-edge bg-canvas/70 p-3 space-y-1.5">
                <div class="flex items-center justify-between gap-2 text-xs font-medium text-ink">
                  <span>{row.name}</span>
                  <span class="tabular-nums text-muted">
                    {row.val}
                    <Show when={row.max !== null}> / {row.max}</Show>
                  </span>
                </div>
                <div class="h-1.5 overflow-hidden rounded-full bg-edge">
                  <div
                    class="h-full rounded-full bg-brand transition-[width] duration-500 ease-out"
                    style={{ width: `${row.ratio}%` }}
                  />
                </div>
                <Show when={row.desc}>
                  <p class="text-[11px] text-muted">{row.desc}</p>
                </Show>
              </div>
            )}
          </For>
        </div>
      </Show>

      <div class="rounded-xl border border-edge bg-canvas/50 p-4 space-y-2">
        <h3 class="text-xs font-semibold uppercase tracking-wider text-muted">Reviewer Feedback</h3>
        <MarkdownView content={props.essay.feedback} />
      </div>
    </section>
  );
}
