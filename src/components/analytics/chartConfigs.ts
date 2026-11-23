import type { ChartConfiguration } from "chart.js/auto";
import type { Schemas } from "@/api/client";

type Attempt = Schemas["UserAttemptSummaryResponse"];
type Essay = Schemas["EssayResponse"];

const essayPct = (e: Essay) => (e.max_score > 0 ? Math.round((e.score / e.max_score) * 100) : 0);

function palette(isDark: boolean) {
  return {
    quiz: isDark ? "#5eead4" : "#0f766e",
    essay: isDark ? "#fbbf24" : "#d97706",
    grid: isDark ? "rgba(148, 163, 184, 0.16)" : "rgba(15, 23, 42, 0.08)",
    tick: isDark ? "#b8c7ce" : "#475569",
  };
}

export function buildTrendConfig(attempts: Attempt[], essays: Essay[], isDark: boolean): ChartConfiguration {
  const c = palette(isDark);
  const qSorted = [...attempts].sort((a, b) => a.completed_at.localeCompare(b.completed_at)).slice(-12);
  const eSorted = [...essays].sort((a, b) => a.created_at.localeCompare(b.created_at)).slice(-12);
  const count = Math.max(qSorted.length, eSorted.length, 1);
  const labels = Array.from({ length: count }, (_, i) => `#${i + 1}`);

  return {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Quiz %",
          data: qSorted.map((a) => Math.round(a.percentage)),
          borderColor: c.quiz,
          backgroundColor: c.quiz,
          tension: 0.3,
          spanGaps: true,
        },
        {
          label: "Essay %",
          data: eSorted.map(essayPct),
          borderColor: c.essay,
          backgroundColor: c.essay,
          tension: 0.3,
          spanGaps: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: c.tick }, grid: { color: c.grid } },
        y: { min: 0, max: 100, ticks: { color: c.tick }, grid: { color: c.grid } },
      },
      plugins: { legend: { labels: { color: c.tick } } },
    },
  };
}

export function buildSubjectConfig(attempts: Attempt[], essays: Essay[], isDark: boolean): ChartConfiguration {
  const c = palette(isDark);
  const buckets = new Map<string, { q: number[]; e: number[] }>();
  const ensure = (raw?: string | null) => {
    const key = (raw ?? "general").trim() || "general";
    let bucket = buckets.get(key);
    if (!bucket) {
      bucket = { q: [], e: [] };
      buckets.set(key, bucket);
    }
    return bucket;
  };
  for (const a of attempts) ensure(a.quiz_subject).q.push(a.percentage);
  for (const e of essays) ensure(e.subject).e.push(essayPct(e));

  const labels = [...buckets.keys()];
  const avg = (vals: number[]) => (vals.length ? Math.round(vals.reduce((s, n) => s + n, 0) / vals.length) : 0);

  return {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Quiz Avg %",
          data: labels.map((l) => avg(buckets.get(l)?.q ?? [])),
          backgroundColor: c.quiz,
          borderRadius: 6,
        },
        {
          label: "Essay Avg %",
          data: labels.map((l) => avg(buckets.get(l)?.e ?? [])),
          backgroundColor: c.essay,
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: c.tick }, grid: { display: false } },
        y: { min: 0, max: 100, ticks: { color: c.tick }, grid: { color: c.grid } },
      },
      plugins: { legend: { labels: { color: c.tick } } },
    },
  };
}
