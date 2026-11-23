import { Plus, Trash2 } from "@lucide/solid";
import { createMemo, createSignal, Errored, For, Loading, refresh, Show } from "solid-js";
import { api, unwrap } from "@/api/client";
import { FilterBar } from "@/components/FilterBar";
import { Pagination } from "@/components/Pagination";
import { QuizAdminDialog } from "@/components/quizzes/QuizAdminDialog";
import { QuizRunner } from "@/components/quizzes/QuizRunner";
import { EmptyState, ErrorBanner, LoadingSkeleton } from "@/components/States";
import { useAuth } from "@/state/auth";
import { usePagedFilters } from "@/state/filters";
import { useToast } from "@/state/toast";

export function QuizzesPage() {
  const auth = useAuth();
  const toast = useToast();
  const { filters, updateFilters, clearFilters, setPage, apiQuery } = usePagedFilters();
  const [selectedId, setSelectedId] = createSignal<number | null>(null);
  const [createOpen, setCreateOpen] = createSignal(false);

  const listPage = createMemo(async () => {
    const query = apiQuery(8);
    return unwrap(api.GET("/api/v1/quizzes", { params: { query } }));
  });

  const effectiveId = createMemo(() => {
    const items = listPage().items;
    const cur = selectedId();
    return cur && items.some((q) => q.id === cur) ? cur : (items[0]?.id ?? null);
  });

  const activeQuiz = createMemo(async () => {
    const id = effectiveId();
    if (!id) return null;
    return unwrap(api.GET("/api/v1/quizzes/{quiz_id}", { params: { path: { quiz_id: id } } }));
  });

  const deleteQuiz = async (id: number) => {
    try {
      await unwrap(api.DELETE("/api/v1/quizzes/{quiz_id}", { params: { path: { quiz_id: id } } }));
      if (selectedId() === id) setSelectedId(null);
      toast.push("Quiz deleted.", "info");
      void refresh(listPage);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Delete failed", "error");
    }
  };

  return (
    <div class="space-y-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 id="page-heading" tabindex="-1" class="text-2xl font-bold text-ink">
            Practice Quizzes
          </h1>
          <p class="text-sm text-muted">Instant server-graded drills with step-by-step explanations.</p>
        </div>
        <Show when={auth.isAdmin()}>
          <button
            type="button"
            class="glass-btn inline-flex items-center gap-1.5 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-brand-ink"
            onClick={() => setCreateOpen(true)}
          >
            <Plus class="h-4 w-4" />
            New Quiz
          </button>
        </Show>
      </div>

      <FilterBar value={filters()} onChange={updateFilters} onClear={clearFilters} />

      <Errored fallback={(err, reset) => <ErrorBanner error={err} onRetry={reset} />}>
        <Loading fallback={<LoadingSkeleton label="Loading quizzes..." />}>
          <Show
            when={listPage().items.length > 0}
            fallback={
              <EmptyState title="No quizzes match" message="Try clearing filters or ask AI Tutor to generate one." />
            }
          >
            <div class="grid gap-5 lg:grid-cols-[20rem_1fr]">
              <div class="space-y-3">
                <For each={listPage().items}>
                  {(q) => (
                    <div
                      class={[
                        "card-hover reading-surface flex items-start justify-between gap-2 rounded-2xl p-4",
                        effectiveId() === q.id ? "border-brand ring-1 ring-brand" : "",
                      ]}
                    >
                      <button type="button" class="flex-1 text-left" onClick={() => setSelectedId(q.id)}>
                        <p class="text-sm font-semibold text-ink">{q.title}</p>
                        <p class="mt-0.5 text-xs text-muted">
                          {q.subject} · {q.difficulty}
                        </p>
                      </button>
                      <Show when={auth.isAdmin()}>
                        <button
                          type="button"
                          aria-label={`Delete ${q.title}`}
                          class="rounded-lg p-1.5 text-muted hover:text-danger"
                          onClick={() => deleteQuiz(q.id)}
                        >
                          <Trash2 class="h-4 w-4" />
                        </button>
                      </Show>
                    </div>
                  )}
                </For>
                <Pagination
                  page={listPage().page}
                  pages={listPage().pages}
                  total={listPage().total}
                  onPageChange={setPage}
                />
              </div>

              <Errored fallback={(err, reset) => <ErrorBanner error={err} onRetry={reset} />}>
                <Loading fallback={<LoadingSkeleton label="Loading quiz questions..." rows={2} />}>
                  <Show when={activeQuiz()} keyed>
                    {(quiz) => <QuizRunner quiz={quiz} />}
                  </Show>
                </Loading>
              </Errored>
            </div>
          </Show>
        </Loading>
      </Errored>

      <QuizAdminDialog
        open={createOpen()}
        onClose={() => setCreateOpen(false)}
        onCreated={() => void refresh(listPage)}
      />
    </div>
  );
}
