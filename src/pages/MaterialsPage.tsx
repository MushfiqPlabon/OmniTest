import { Plus } from "@lucide/solid";
import { createMemo, createSignal, Errored, For, Loading, refresh, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { FilterBar } from "@/components/FilterBar";
import { MaterialAdminActions } from "@/components/materials/MaterialAdminActions";
import { MaterialAdminDialog } from "@/components/materials/MaterialAdminDialog";
import { MaterialCard } from "@/components/materials/MaterialCard";
import { MaterialReader } from "@/components/materials/MaterialReader";
import { Pagination } from "@/components/Pagination";
import { EmptyState, ErrorBanner, LoadingSkeleton } from "@/components/States";
import { useAuth } from "@/state/auth";
import { usePagedFilters } from "@/state/filters";
import { useToast } from "@/state/toast";

export function MaterialsPage() {
  const { isAdmin } = useAuth();
  const toast = useToast();
  const { filters, updateFilters, clearFilters, setPage, apiQuery } = usePagedFilters();
  const [selected, setSelected] = createSignal<Schemas["MaterialResponse"] | null>(null);
  const [dialogOpen, setDialogOpen] = createSignal(false);
  const [editing, setEditing] = createSignal<Schemas["MaterialResponse"] | null>(null);
  const [ingestingId, setIngestingId] = createSignal<number | null>(null);

  const materials = createMemo(async () => unwrap(api.GET("/api/v1/materials", { params: { query: apiQuery(9) } })));

  const reingest = async (id: number) => {
    setIngestingId(id);
    try {
      const res = await unwrap(
        api.POST("/api/v1/materials/{material_id}/ingest", { params: { path: { material_id: id } } }),
      );
      toast.push(`Re-ingested (${res.chunks_created} chunks indexed)`, "success");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Re-ingest failed", "error");
    } finally {
      setIngestingId(null);
    }
  };

  const remove = async (id: number) => {
    try {
      await unwrap(api.DELETE("/api/v1/materials/{material_id}", { params: { path: { material_id: id } } }));
      if (selected()?.id === id) setSelected(null);
      void refresh(materials);
      toast.push("Study material deleted", "info");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Delete failed", "error");
    }
  };

  const actionsFor = (item: Schemas["MaterialResponse"]) => (
    <Show when={isAdmin()}>
      <MaterialAdminActions
        busy={ingestingId() === item.id}
        onEdit={() => {
          setEditing(item);
          setDialogOpen(true);
        }}
        onReingest={() => void reingest(item.id)}
        onDelete={() => void remove(item.id)}
      />
    </Show>
  );

  return (
    <div class="space-y-5">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 id="page-heading" tabindex="-1" class="text-2xl font-bold tracking-tight text-ink focus:outline-none">
            Study Library
          </h1>
          <p class="text-sm text-muted">Browse curated reference guides with Markdown and LaTeX notation.</p>
        </div>
        <Show when={isAdmin()}>
          <button
            type="button"
            class="glass-btn inline-flex items-center gap-1.5 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-brand-ink"
            onClick={() => {
              setEditing(null);
              setDialogOpen(true);
            }}
          >
            <Plus class="h-4 w-4" /> Add Material
          </button>
        </Show>
      </div>

      <Show
        when={selected()}
        keyed
        fallback={
          <>
            <FilterBar value={filters()} onChange={updateFilters} onClear={clearFilters} />
            <Errored
              fallback={(err, reset) => (
                <ErrorBanner
                  error={err}
                  onRetry={() => {
                    reset();
                    void refresh(materials);
                  }}
                />
              )}
            >
              <Loading fallback={<LoadingSkeleton label="Loading study guides..." rows={6} />}>
                <Show
                  when={materials().items.length > 0}
                  fallback={
                    <EmptyState
                      title="No study guides found"
                      message="Try clearing filters or ask an admin to upload materials."
                    />
                  }
                >
                  <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <For each={materials().items}>
                      {(m) => <MaterialCard material={m} onRead={setSelected} actions={actionsFor(m)} />}
                    </For>
                  </div>
                  <Pagination
                    page={materials().page}
                    pages={materials().pages}
                    total={materials().total}
                    onPageChange={setPage}
                  />
                </Show>
              </Loading>
            </Errored>
          </>
        }
      >
        {(m) => <MaterialReader material={m} onBack={() => setSelected(null)} actions={actionsFor(m)} />}
      </Show>

      <MaterialAdminDialog
        open={dialogOpen()}
        editing={editing()}
        onClose={() => setDialogOpen(false)}
        onSaved={() => {
          setSelected(null);
          void refresh(materials);
        }}
      />
    </div>
  );
}
