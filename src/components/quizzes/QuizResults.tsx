import { CheckCircle2, XCircle } from "@lucide/solid";
import { For, Show } from "solid-js";
import type { Schemas } from "@/api/client";

export function QuizResults(props: { result: Schemas["AttemptResponse"] }) {
  return (
    <div class="glass-surface space-y-4 rounded-2xl p-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="text-base font-bold text-ink">Quiz Results</h3>
          <p class="text-xs text-muted">{props.result.feedback}</p>
        </div>
        <div class="flex items-center gap-3 font-mono text-sm font-semibold tabular-nums">
          <span class="rounded-xl bg-surface px-3 py-1.5 text-ink">
            {props.result.score} / {props.result.max_score}
          </span>
          <span class="rounded-xl bg-brand px-3 py-1.5 text-brand-ink">{props.result.percentage}%</span>
        </div>
      </div>

      <div class="space-y-2.5">
        <For each={props.result.details}>
          {(item, idx) => (
            <div class="reading-surface rounded-xl p-3.5 text-sm">
              <div class="flex items-start justify-between gap-2">
                <p class="font-medium text-ink">
                  Q{idx() + 1}. {item.prompt}
                </p>
                {item.is_correct ? (
                  <CheckCircle2 class="h-4 w-4 shrink-0 text-ok" />
                ) : (
                  <XCircle class="h-4 w-4 shrink-0 text-danger" />
                )}
              </div>
              <p class="mt-1 text-xs text-muted">
                Your answer: <span class="font-mono text-ink">{item.student_answer || "—"}</span> · Correct:{" "}
                <span class="font-mono text-ok">{item.correct_answer}</span>
              </p>
              <Show when={item.explanation}>
                <p class="mt-1 text-xs text-muted">{item.explanation}</p>
              </Show>
            </div>
          )}
        </For>
      </div>
    </div>
  );
}
