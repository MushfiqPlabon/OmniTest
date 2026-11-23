import { createSignal, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { EssayRubricFields } from "@/components/essays/EssayRubricFields";
import { GlassDialog } from "@/components/GlassDialog";
import { useToast } from "@/state/toast";

type Diff = "easy" | "medium" | "hard";
const INPUT_CLS = "w-full rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink";

const defaultCriteria = (): Schemas["RubricCriterion"][] => [
  { name: "Thesis & Clarity", max: 4, desc: "Clear central claim and focus" },
  { name: "Evidence & Depth", max: 4, desc: "Accurate reasoning and examples" },
  { name: "Organization & Mechanics", max: 4, desc: "Coherent flow and precision" },
];

function EssayPromptForm(props: {
  editing?: Schemas["PromptResponse"] | null;
  onClose: () => void;
  onCreated: () => void;
}) {
  const toast = useToast();
  const [subject, setSubject] = createSignal(() => props.editing?.subject ?? "");
  const [topic, setTopic] = createSignal(() => props.editing?.topic ?? "");
  const [difficulty, setDifficulty] = createSignal<Diff>(() => (props.editing?.difficulty as Diff) ?? "medium");
  const [promptText, setPromptText] = createSignal(() => props.editing?.prompt_text ?? "");
  const [maxScore, setMaxScore] = createSignal(() => props.editing?.rubric.max_score ?? 12);
  const [criteria, setCriteria] = createSignal(() =>
    props.editing?.rubric.criteria?.length ? props.editing.rubric.criteria.map((c) => ({ ...c })) : defaultCriteria(),
  );
  const [saving, setSaving] = createSignal(false);

  const submit = async (e: SubmitEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const body = {
        subject: subject().trim(),
        topic: topic().trim(),
        difficulty: difficulty(),
        prompt_text: promptText().trim(),
        rubric: { max_score: Number(maxScore()) || 12, criteria: criteria().filter((c) => c.name.trim()) },
      };
      if (props.editing) {
        const id = props.editing.id;
        await unwrap(api.PATCH("/api/v1/essays/prompts/{prompt_id}", { params: { path: { prompt_id: id } }, body }));
        toast.push("Essay prompt updated", "success");
      } else {
        await unwrap(api.POST("/api/v1/essays/prompts", { body }));
        toast.push("Essay prompt created", "success");
      }
      props.onCreated();
      props.onClose();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Failed to save prompt", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form class="space-y-4 text-sm" onSubmit={submit}>
      <div class="grid gap-3 sm:grid-cols-3">
        <label class="space-y-1 text-xs font-medium text-ink">
          <span>Subject</span>
          <input class={INPUT_CLS} required value={subject()} onInput={(e) => setSubject(e.currentTarget.value)} />
        </label>
        <label class="space-y-1 text-xs font-medium text-ink">
          <span>Topic</span>
          <input class={INPUT_CLS} required value={topic()} onInput={(e) => setTopic(e.currentTarget.value)} />
        </label>
        <label class="space-y-1 text-xs font-medium text-ink">
          <span>Difficulty</span>
          <select class={INPUT_CLS} value={difficulty()} onChange={(e) => setDifficulty(e.currentTarget.value as Diff)}>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>
      </div>
      <label class="block space-y-1 text-xs font-medium text-ink">
        <span>Prompt instructions</span>
        <textarea
          class={`${INPUT_CLS} min-h-24`}
          required
          value={promptText()}
          onInput={(e) => setPromptText(e.currentTarget.value)}
        />
      </label>
      <EssayRubricFields
        maxScore={maxScore()}
        onMaxScore={setMaxScore}
        criteria={criteria()}
        onChangeCriteria={setCriteria}
      />
      <div class="flex justify-end gap-2 pt-1">
        <button
          type="button"
          class="rounded-xl border border-edge px-4 py-2 text-xs font-medium text-muted"
          onClick={() => props.onClose()}
        >
          Cancel
        </button>
        <button
          type="submit"
          class="glass-btn rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-brand-ink disabled:opacity-50"
          disabled={saving()}
        >
          {saving() ? "Saving..." : props.editing ? "Save changes" : "Create prompt"}
        </button>
      </div>
    </form>
  );
}

export function EssayAdminDialog(props: {
  open: boolean;
  editing?: Schemas["PromptResponse"] | null;
  onClose: () => void;
  onCreated: () => void;
}) {
  return (
    <GlassDialog
      open={props.open}
      title={props.editing ? "Edit essay prompt" : "New essay prompt"}
      onClose={() => props.onClose()}
    >
      <Show when={props.open}>
        <EssayPromptForm editing={props.editing} onClose={() => props.onClose()} onCreated={() => props.onCreated()} />
      </Show>
    </GlassDialog>
  );
}
