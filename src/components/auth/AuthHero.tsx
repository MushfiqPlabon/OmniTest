import { GraduationCap, Shield, Sparkles } from "@lucide/solid";
import { Show } from "solid-js";

const SHOW_DEMO = (import.meta.env.VITE_SHOW_DEMO_LOGIN ?? "true") !== "false";

export function AuthHero(props: { pending: boolean; onDemo: (role: "student" | "admin") => void }) {
  return (
    <section class="space-y-4">
      <span class="inline-flex items-center gap-1.5 rounded-full border border-edge bg-surface px-3 py-1 text-xs font-medium text-brand">
        <Sparkles class="h-3.5 w-3.5" />
        GED & Digital SAT Prep
      </span>
      <h1 id="page-heading" tabindex="-1" class="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
        Practice with calm, rubric-grounded feedback.
      </h1>
      <p class="max-w-lg text-sm leading-relaxed text-muted">
        Ask questions grounded in verified study guides, generate custom practice quizzes, get 12-point essay
        evaluations, and track your readiness over time.
      </p>

      <Show when={SHOW_DEMO}>
        <div class="reading-surface rounded-2xl p-4">
          <p class="mb-2.5 text-xs font-semibold uppercase tracking-wide text-muted">Instant Demo Access</p>
          <div class="flex flex-wrap gap-2.5">
            <button
              type="button"
              disabled={props.pending}
              class="glass-btn inline-flex items-center gap-2 rounded-xl bg-brand px-4 py-2 text-sm font-medium text-brand-ink disabled:opacity-50"
              onClick={() => props.onDemo("student")}
            >
              <GraduationCap class="h-4 w-4" /> Demo Student
            </button>
            <button
              type="button"
              disabled={props.pending}
              class="glass-btn inline-flex items-center gap-2 rounded-xl border border-edge bg-canvas px-4 py-2 text-sm font-medium text-ink disabled:opacity-50"
              onClick={() => props.onDemo("admin")}
            >
              <Shield class="h-4 w-4 text-accent" /> Demo Admin
            </button>
          </div>
        </div>
      </Show>
    </section>
  );
}
