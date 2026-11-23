import { createSignal, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { GlassDialog } from "@/components/GlassDialog";
import { useToast } from "@/state/toast";

type Diff = "easy" | "medium" | "hard";
const INPUT_CLS = "w-full rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink";

function EditQuizForm(props: { quiz: Schemas["QuizResponse"]; onClose: () => void; onSaved: () => void }) {
  const toast = useToast();
  const [title, setTitle] = createSignal(() => props.quiz.title);
  const [subject, setSubject] = createSignal(() => props.quiz.subject);
  const [topic, setTopic] = createSignal(() => props.quiz.topic);
  const [difficulty, setDifficulty] = createSignal<Diff>(() => (props.quiz.difficulty as Diff) ?? "medium");
  const [saving, setSaving] = createSignal(false);

  const save = async (e: SubmitEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await unwrap(
        api.PATCH("/api/v1/quizzes/{quiz_id}", {
          params: { path: { quiz_id: props.quiz.id } },
          body: { title: title().trim(), subject: subject().trim(), topic: topic().trim(), difficulty: difficulty() },
        }),
      );
      toast.push("Quiz updated", "success");
      props.onSaved();
      props.onClose();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Update failed", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form class="space-y-3 text-sm" onSubmit={save}>
      <label class="block space-y-1 text-xs font-medium text-ink">
        <span>Title</span>
        <input class={INPUT_CLS} required value={title()} onInput={(e) => setTitle(e.currentTarget.value)} />
      </label>
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
            <option value="easy">easy</option>
            <option value="medium">medium</option>
            <option value="hard">hard</option>
          </select>
        </label>
      </div>
      <div class="flex justify-end gap-2 pt-1">
        <button
          type="button"
          class="rounded-xl border border-edge px-4 py-2 text-xs text-muted"
          onClick={() => props.onClose()}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={saving()}
          class="glass-btn rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-brand-ink"
        >
          {saving() ? "Saving..." : "Save changes"}
        </button>
      </div>
    </form>
  );
}

export function QuizEditDialog(props: {
  quiz: Schemas["QuizResponse"] | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  return (
    <GlassDialog open={Boolean(props.quiz)} title="Edit quiz metadata" onClose={() => props.onClose()}>
      <Show when={props.quiz} keyed>
        {(q) => <EditQuizForm quiz={q} onClose={() => props.onClose()} onSaved={() => props.onSaved()} />}
      </Show>
    </GlassDialog>
  );
}
