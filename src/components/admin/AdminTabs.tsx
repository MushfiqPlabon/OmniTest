import { createSignal, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { AdminMaterialsTable } from "@/components/admin/AdminMaterialsTable";
import { AdminPromptsTable } from "@/components/admin/AdminPromptsTable";
import { AdminQuizzesPanel } from "@/components/admin/AdminQuizzesPanel";
import { EssayAdminDialog } from "@/components/essays/EssayAdminDialog";
import { MaterialAdminDialog } from "@/components/materials/MaterialAdminDialog";
import { useToast } from "@/state/toast";

export function AdminTabs(props: {
  materials: Schemas["MaterialResponse"][];
  quizzes: Schemas["QuizResponse"][];
  prompts: Schemas["PromptResponse"][];
  onRefresh: () => void;
}) {
  const toast = useToast();
  const [tab, setTab] = createSignal<"materials" | "quizzes" | "prompts">("materials");
  const [matEditing, setMatEditing] = createSignal<Schemas["MaterialResponse"] | null>(null);
  const [promptEditing, setPromptEditing] = createSignal<Schemas["PromptResponse"] | null>(null);
  const [ingestingId, setIngestingId] = createSignal<number | null>(null);

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

  const removeItem = async (kind: "material" | "prompt", id: number) => {
    try {
      if (kind === "material")
        await unwrap(api.DELETE("/api/v1/materials/{material_id}", { params: { path: { material_id: id } } }));
      else await unwrap(api.DELETE("/api/v1/essays/prompts/{prompt_id}", { params: { path: { prompt_id: id } } }));
      toast.push(kind === "material" ? "Study material deleted" : "Prompt deleted", "info");
      props.onRefresh();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Delete failed", "error");
    }
  };

  return (
    <>
      <div class="inline-flex rounded-xl border border-edge bg-surface p-1 text-xs" role="tablist">
        {(["materials", "quizzes", "prompts"] as const).map((t) => (
          <button
            type="button"
            role="tab"
            aria-selected={tab() === t ? "true" : "false"}
            class={[
              "rounded-lg px-3.5 py-1.5 font-medium transition-colors",
              tab() === t ? "bg-accent text-brand-ink" : "text-muted hover:text-ink",
            ]}
            onClick={() => setTab(t)}
          >
            {t === "materials" ? "Materials" : t === "quizzes" ? "Quizzes & Attempts" : "Essay Prompts"}
          </button>
        ))}
      </div>

      <Show when={tab() === "materials"}>
        <AdminMaterialsTable
          items={props.materials}
          ingestingId={ingestingId()}
          onEdit={(m) => setMatEditing(m)}
          onReingest={(id) => void reingest(id)}
          onDelete={(id) => void removeItem("material", id)}
        />
      </Show>
      <Show when={tab() === "quizzes"}>
        <AdminQuizzesPanel items={props.quizzes} onChanged={() => props.onRefresh()} />
      </Show>
      <Show when={tab() === "prompts"}>
        <AdminPromptsTable
          items={props.prompts}
          onEdit={(p) => setPromptEditing(p)}
          onDelete={(id) => void removeItem("prompt", id)}
        />
      </Show>

      <MaterialAdminDialog
        open={Boolean(matEditing())}
        editing={matEditing()}
        onClose={() => setMatEditing(null)}
        onSaved={() => props.onRefresh()}
      />
      <EssayAdminDialog
        open={Boolean(promptEditing())}
        editing={promptEditing()}
        onClose={() => setPromptEditing(null)}
        onCreated={() => props.onRefresh()}
      />
    </>
  );
}
