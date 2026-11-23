import { createSignal } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { EssayRubricFields } from "@/components/essays/EssayRubricFields";
import { GlassDialog } from "@/components/GlassDialog";
import { useToast } from "@/state/toast";

interface EssayAdminDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

type Diff = "easy" | "medium" | "hard";
const INPUT_CLS = "w-full rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink";

const defaultCriteria = (): Schemas["RubricCriterion"][] => [
  { name: "Thesis & Clarity", max: 4, desc: "Clear central claim and focus" },
  { name: "Evidence & Depth", max: 4, desc: "Accurate reasoning and examples" },
  { name: "Organization & Mechanics", max: 4, desc: "Coherent flow and precision" },
];

export function EssayAdminDialog(props: EssayAdminDialogProps) {
  const toast = useToast();
  const [subject, setSubject] = createSignal("");
  const [topic, setTopic] = createSignal("");
  const [difficulty, setDifficulty] = createSignal<Diff>("medium");
  const [promptText, setPromptText] = createSignal("");
  const [maxScore, setMaxScore] = createSignal(12);
  const [criteria, setCriteria] = createSignal(defaultCriteria());
  const [saving, setSaving] = createSignal(false);

  const submit = async (e: SubmitEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await unwrap(
        api.POST("/api/v1/essays/prompts", {
          body: {
            subject: subject().trim(),
            topic: topic().trim(),
            difficulty: difficulty(),
            prompt_text: promptText().trim(),
            rubric: {
              max_score: Number(maxScore()) || 12,
              criteria: criteria().filter((c) => c.name.trim()),
            },
          },
        }),
      );
      toast.push("Essay prompt created", "success");
      setSubject("");
      setTopic("");
      setPromptText("");
      setCriteria(defaultCriteria());
      props.onCreated();
      props.onClose();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Failed to create prompt", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <GlassDialog open={props.open} title="New essay prompt" onClose={() => props.onClose()}>
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
            <select
              class={INPUT_CLS}
              value={difficulty()}
              onChange={(e) => setDifficulty(e.currentTarget.value as Diff)}
            >
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
            placeholder="Ask students to analyze, compare, or argue a well-defined thesis..."
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
            {saving() ? "Creating..." : "Create prompt"}
          </button>
        </div>
      </form>
    </GlassDialog>
  );
}
