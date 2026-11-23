import { For, Show } from "solid-js";
import type { Schemas } from "@/api/client";

const shortDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
const essayPct = (e: Schemas["EssayResponse"]) => (e.max_score > 0 ? Math.round((e.score / e.max_score) * 100) : 0);

export function RecentActivity(props: {
  attempts: Schemas["UserAttemptSummaryResponse"][];
  essays: Schemas["EssayResponse"][];
}) {
  return (
    <div class="grid gap-5 lg:grid-cols-2">
      <section class="reading-surface rounded-2xl p-5 space-y-3">
        <h2 class="text-sm font-semibold text-ink">Recent Quiz Attempts</h2>
        <Show when={props.attempts.length > 0} fallback={<p class="text-xs text-muted">No quiz attempts yet.</p>}>
          <ul class="divide-y divide-edge text-sm">
            <For each={props.attempts.slice(0, 5)}>
              {(a) => (
                <li class="flex items-center justify-between gap-3 py-2.5">
                  <div class="min-w-0">
                    <p class="truncate font-medium text-ink">{a.quiz_title ?? `Quiz #${a.quiz_id}`}</p>
                    <p class="text-xs text-muted">
                      {a.quiz_subject ?? "general"} · {shortDate(a.completed_at)}
                    </p>
                  </div>
                  <span class="shrink-0 font-mono text-xs font-semibold text-brand tabular-nums">
                    {a.score}/{a.max_score} ({Math.round(a.percentage)}%)
                  </span>
                </li>
              )}
            </For>
          </ul>
        </Show>
      </section>

      <section class="reading-surface rounded-2xl p-5 space-y-3">
        <h2 class="text-sm font-semibold text-ink">Recent Essay Evaluations</h2>
        <Show when={props.essays.length > 0} fallback={<p class="text-xs text-muted">No graded essays yet.</p>}>
          <ul class="divide-y divide-edge text-sm">
            <For each={props.essays.slice(0, 5)}>
              {(e) => (
                <li class="flex items-center justify-between gap-3 py-2.5">
                  <div class="min-w-0">
                    <p class="truncate font-medium text-ink capitalize">{e.subject ?? `Prompt #${e.prompt_id}`}</p>
                    <p class="text-xs text-muted">{shortDate(e.created_at)}</p>
                  </div>
                  <span class="shrink-0 font-mono text-xs font-semibold text-accent tabular-nums">
                    {e.score}/{e.max_score} ({essayPct(e)}%)
                  </span>
                </li>
              )}
            </For>
          </ul>
        </Show>
      </section>
    </div>
  );
}
