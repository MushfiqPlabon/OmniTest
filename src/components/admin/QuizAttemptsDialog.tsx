import { For, Show } from "solid-js";
import type { Schemas } from "@/api/client";
import { GlassDialog } from "@/components/GlassDialog";

const shortDate = (iso: string) => new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });

export function QuizAttemptsDialog(props: {
  quiz: Schemas["QuizResponse"] | null;
  attempts: Schemas["AttemptSummaryResponse"][];
  loading: boolean;
  onClose: () => void;
}) {
  return (
    <GlassDialog
      open={Boolean(props.quiz)}
      title={`Attempts · ${props.quiz?.title ?? ""}`}
      onClose={() => props.onClose()}
    >
      <Show when={!props.loading} fallback={<p class="text-xs text-muted">Loading student attempts...</p>}>
        <Show
          when={props.attempts.length > 0}
          fallback={<p class="text-xs text-muted">No student attempts recorded for this quiz yet.</p>}
        >
          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs">
              <thead class="border-b border-edge uppercase tracking-wider text-muted">
                <tr>
                  <th class="py-2 pr-3 font-semibold">Attempt</th>
                  <th class="py-2 pr-3 font-semibold">User</th>
                  <th class="py-2 pr-3 font-semibold">Score</th>
                  <th class="py-2 font-semibold">Date</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-edge">
                <For each={props.attempts}>
                  {(a) => {
                    const pct = a.max_score > 0 ? Math.round((a.score / a.max_score) * 100) : 0;
                    return (
                      <tr>
                        <td class="py-2 pr-3 font-mono text-ink tabular-nums">#{a.id}</td>
                        <td class="py-2 pr-3 text-muted tabular-nums">User #{a.user_id}</td>
                        <td class="py-2 pr-3 font-mono font-semibold text-brand tabular-nums">
                          {a.score}/{a.max_score} ({pct}%)
                        </td>
                        <td class="py-2 text-muted">{shortDate(a.completed_at)}</td>
                      </tr>
                    );
                  }}
                </For>
              </tbody>
            </table>
          </div>
        </Show>
      </Show>
    </GlassDialog>
  );
}
