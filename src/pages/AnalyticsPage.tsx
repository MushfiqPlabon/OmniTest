import { Award, CheckCircle2, PenTool, TrendingUp } from "@lucide/solid";
import type { JSX } from "@solidjs/web";
import { createMemo, Errored, Loading, refresh, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { buildSubjectConfig, buildTrendConfig } from "@/components/analytics/chartConfigs";
import { RecentActivity } from "@/components/analytics/RecentActivity";
import { ScoreChart } from "@/components/ScoreChart";
import { EmptyState, ErrorBanner, LoadingSkeleton } from "@/components/States";

const avgOf = (vals: number[]) => (vals.length ? `${Math.round(vals.reduce((s, n) => s + n, 0) / vals.length)}%` : "—");
const essayPct = (e: Schemas["EssayResponse"]) => (e.max_score > 0 ? Math.round((e.score / e.max_score) * 100) : 0);

function KpiCard(props: { label: string; value: string | number; sub?: string; icon: JSX.Element }) {
  return (
    <div class="reading-surface rounded-2xl p-4">
      <div class="flex items-center justify-between text-xs font-medium text-muted">
        <span>{props.label}</span>
        {props.icon}
      </div>
      <p class="mt-2 text-2xl font-bold tracking-tight text-ink tabular-nums">{props.value}</p>
      <Show when={props.sub}>
        <p class="mt-0.5 text-xs text-muted">{props.sub}</p>
      </Show>
    </div>
  );
}

export function AnalyticsPage() {
  const summary = createMemo(async () => {
    const [attempts, essays] = await Promise.all([
      unwrap(api.GET("/api/v1/quizzes/attempts/my", { params: { query: { limit: 50, offset: 0 } } })),
      unwrap(api.GET("/api/v1/essays/my", { params: { query: { limit: 50, offset: 0 } } })),
    ]);
    return { attempts, essays };
  });

  return (
    <div class="space-y-6">
      <div>
        <h1 id="page-heading" tabindex="-1" class="text-2xl font-bold tracking-tight text-ink focus:outline-none">
          Readiness Analytics
        </h1>
        <p class="text-sm text-muted">Track quiz accuracy, essay rubric progress, and subject balance over time.</p>
      </div>

      <Errored
        fallback={(err, reset) => (
          <ErrorBanner
            error={err}
            onRetry={() => {
              reset();
              void refresh(summary);
            }}
          />
        )}
      >
        <Loading fallback={<LoadingSkeleton label="Loading performance analytics..." rows={4} />}>
          <Show
            when={summary().attempts.length > 0 || summary().essays.length > 0}
            fallback={
              <EmptyState
                title="No graded activity yet"
                message="Complete a practice quiz or submit an essay to see score trends and subject averages."
              />
            }
          >
            <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <KpiCard
                label="Quizzes Taken"
                value={summary().attempts.length}
                icon={<CheckCircle2 class="h-4 w-4 text-brand" />}
              />
              <KpiCard
                label="Avg Quiz Score"
                value={avgOf(summary().attempts.map((a) => a.percentage))}
                icon={<TrendingUp class="h-4 w-4 text-brand" />}
              />
              <KpiCard
                label="Essays Graded"
                value={summary().essays.length}
                icon={<PenTool class="h-4 w-4 text-brand" />}
              />
              <KpiCard
                label="Avg Essay Score"
                value={avgOf(summary().essays.map(essayPct))}
                icon={<Award class="h-4 w-4 text-brand" />}
              />
            </div>

            <div class="grid gap-5 lg:grid-cols-2">
              <ScoreChart
                title="Recent Score Trend (%)"
                buildConfig={(isDark) => buildTrendConfig(summary().attempts, summary().essays, isDark)}
              />
              <ScoreChart
                title="Average Score by Subject (%)"
                buildConfig={(isDark) => buildSubjectConfig(summary().attempts, summary().essays, isDark)}
              />
            </div>

            <RecentActivity attempts={summary().attempts} essays={summary().essays} />
          </Show>
        </Loading>
      </Errored>
    </div>
  );
}
