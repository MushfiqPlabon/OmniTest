import { History, Plus } from "@lucide/solid";
import { createMemo, createSignal, Errored, For, Loading, refresh, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { EssayAdminDialog } from "@/components/essays/EssayAdminDialog";
import { EssayHistoryList } from "@/components/essays/EssayHistoryList";
import { EssayPromptCard } from "@/components/essays/EssayPromptCard";
import { EssayWorkspace } from "@/components/essays/EssayWorkspace";
import { FilterBar } from "@/components/FilterBar";
import { Pagination } from "@/components/Pagination";
import { EmptyState, ErrorBanner, LoadingSkeleton } from "@/components/States";
import { useAuth } from "@/state/auth";
import { usePagedFilters } from "@/state/filters";
import { useToast } from "@/state/toast";

export function EssaysPage() {
  const { isAdmin } = useAuth();
  const toast = useToast();
  const { filters, updateFilters, clearFilters, setPage, apiQuery } = usePagedFilters();
  const [selected, setSelected] = createSignal<Schemas["PromptResponse"] | null>(null);
  const [viewHistory, setViewHistory] = createSignal(false);
  const [adminOpen, setAdminOpen] = createSignal(false);

  const prompts = createMemo(async () => {
    const query = apiQuery(8);
    return unwrap(api.GET("/api/v1/essays/prompts", { params: { query } }));
  });

  const history = createMemo(async () => {
    if (!viewHistory()) return [];
    return unwrap(api.GET("/api/v1/essays/my", { params: { query: { limit: 15, offset: 0 } } }));
  });

  const removePrompt = async (id: number) => {
    try {
      await unwrap(api.DELETE("/api/v1/essays/prompts/{prompt_id}", { params: { path: { prompt_id: id } } }));
      if (selected()?.id === id) setSelected(null);
      void refresh(prompts);
      toast.push("Prompt deleted", "info");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Delete failed", "error");
    }
  };

  return (
    <div class="space-y-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 id="page-heading" tabindex="-1" class="text-2xl font-bold tracking-tight text-ink focus:outline-none">
            Essay Studio
          </h1>
          <p class="text-sm text-muted">Draft long-form responses against rubric criteria for detailed evaluation.</p>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="glass-btn inline-flex items-center gap-1.5 rounded-xl border border-edge bg-surface px-3 py-2 text-xs font-medium text-ink"
            aria-pressed={viewHistory() ? "true" : "false"}
            onClick={() => {
              setSelected(null);
              setViewHistory((v) => !v);
            }}
          >
            <History class="h-4 w-4" />
            {viewHistory() ? "Browse Prompts" : "My Submissions"}
          </button>
          <Show when={isAdmin()}>
            <button
              type="button"
              class="glass-btn inline-flex items-center gap-1.5 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-brand-ink"
              onClick={() => setAdminOpen(true)}
            >
              <Plus class="h-4 w-4" /> New Prompt
            </button>
          </Show>
        </div>
      </div>

      <Show
        when={selected()}
        keyed
        fallback={
          <Show
            when={!viewHistory()}
            fallback={<EssayHistoryList items={() => history()} onRetry={() => void refresh(history)} />}
          >
            <FilterBar value={filters()} onChange={updateFilters} onClear={clearFilters} />
            <Errored
              fallback={(err, reset) => (
                <ErrorBanner
                  error={err}
                  onRetry={() => {
                    reset();
                    void refresh(prompts);
                  }}
                />
              )}
            >
              <Loading fallback={<LoadingSkeleton label="Loading essay prompts..." rows={4} />}>
                <Show
                  when={prompts().items.length > 0}
                  fallback={<EmptyState title="No prompts found" message="Adjust your filters or check back later." />}
                >
                  <div class="grid gap-4 md:grid-cols-2">
                    <For each={prompts().items}>
                      {(p) => (
                        <EssayPromptCard
                          prompt={p}
                          isAdmin={isAdmin()}
                          onWrite={(item) => {
                            setViewHistory(false);
                            setSelected(item);
                          }}
                          onDelete={removePrompt}
                        />
                      )}
                    </For>
                  </div>
                  <Pagination
                    page={prompts().page}
                    pages={prompts().pages}
                    total={prompts().total}
                    onPageChange={setPage}
                  />
                </Show>
              </Loading>
            </Errored>
          </Show>
        }
      >
        {(p) => <EssayWorkspace prompt={p} onBack={() => setSelected(null)} onGraded={() => void refresh(history)} />}
      </Show>

      <EssayAdminDialog
        open={adminOpen()}
        onClose={() => setAdminOpen(false)}
        onCreated={() => void refresh(prompts)}
      />
    </div>
  );
}
