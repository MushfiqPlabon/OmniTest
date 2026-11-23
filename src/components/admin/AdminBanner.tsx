import { Activity, BookOpen, CheckSquare, FileText, Plus, Shield } from "@lucide/solid";

export function AdminHeader(props: { onNewMaterial: () => void; onNewQuiz: () => void; onNewPrompt: () => void }) {
  return (
    <div class="reading-surface flex flex-wrap items-center justify-between gap-4 rounded-2xl border-l-4 border-l-accent p-5">
      <div>
        <span class="inline-flex items-center gap-1.5 rounded-full bg-accent/15 px-2.5 py-0.5 text-xs font-semibold text-accent">
          <Shield class="h-3.5 w-3.5" /> Administrator Workspace
        </span>
        <h1
          id="page-heading"
          tabindex="-1"
          class="mt-1.5 text-2xl font-bold tracking-tight text-ink focus:outline-none"
        >
          Admin Console
        </h1>
        <p class="text-sm text-muted">
          Manage RAG study materials, practice quizzes, student attempt logs, and essay rubrics.
        </p>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1 rounded-xl bg-brand px-3.5 py-2 text-xs font-semibold text-brand-ink"
          onClick={() => props.onNewMaterial()}
        >
          <Plus class="h-3.5 w-3.5" /> Material
        </button>
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1 rounded-xl border border-edge bg-surface px-3.5 py-2 text-xs font-semibold text-ink"
          onClick={() => props.onNewQuiz()}
        >
          <Plus class="h-3.5 w-3.5" /> Quiz
        </button>
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1 rounded-xl border border-edge bg-surface px-3.5 py-2 text-xs font-semibold text-ink"
          onClick={() => props.onNewPrompt()}
        >
          <Plus class="h-3.5 w-3.5" /> Essay Prompt
        </button>
      </div>
    </div>
  );
}

export function AdminKpiStrip(props: { materials: number; quizzes: number; prompts: number; healthText: string }) {
  const cards = () => [
    { label: "Materials", val: props.materials, icon: <BookOpen class="h-4 w-4 text-brand" /> },
    { label: "Quizzes", val: props.quizzes, icon: <CheckSquare class="h-4 w-4 text-brand" /> },
    { label: "Essay Prompts", val: props.prompts, icon: <FileText class="h-4 w-4 text-brand" /> },
    { label: "API Health", val: props.healthText, icon: <Activity class="h-4 w-4 text-ok" /> },
  ];

  return (
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards().map((card) => (
        <div class="reading-surface rounded-2xl p-4">
          <div class="flex items-center justify-between text-xs font-medium text-muted">
            <span>{card.label}</span>
            {card.icon}
          </div>
          <p class="mt-2 text-xl font-bold text-ink tabular-nums">{card.val}</p>
        </div>
      ))}
    </div>
  );
}
