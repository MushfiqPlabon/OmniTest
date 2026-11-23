import { createSignal, Show } from "solid-js";
import { api, unwrap } from "@/api/client";
import { GlassDialog } from "@/components/GlassDialog";
import { ErrorBanner } from "@/components/States";
import { useToast } from "@/state/toast";

const INPUT_CLS = "w-full rounded-xl border border-edge bg-canvas px-3 py-2 text-ink";

export function QuizAdminDialog(props: { open: boolean; onClose: () => void; onCreated: () => void }) {
  const toast = useToast();
  const [title, setTitle] = createSignal("");
  const [subject, setSubject] = createSignal("math");
  const [topic, setTopic] = createSignal("linear equations");
  const [difficulty, setDifficulty] = createSignal<"easy" | "medium" | "hard">("medium");
  const [prompt, setPrompt] = createSignal("");
  const [optionsText, setOptionsText] = createSignal("A. x = 2\nB. x = 4\nC. x = 6\nD. x = 8");
  const [correct, setCorrect] = createSignal("B");
  const [explanation, setExplanation] = createSignal("");
  const [saving, setSaving] = createSignal(false);
  const [err, setErr] = createSignal<string | null>(null);

  const submit = async (e: SubmitEvent) => {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    try {
      const options = optionsText()
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean);
      await unwrap(
        api.POST("/api/v1/quizzes", {
          body: {
            title: title().trim(),
            subject: subject(),
            topic: topic().trim(),
            difficulty: difficulty(),
            questions: [
              {
                type: options.length > 0 ? "mcq" : "short_answer",
                prompt: prompt().trim(),
                options: options.length > 0 ? options : null,
                correct_answer: correct().trim(),
                explanation: explanation().trim() || null,
                order_num: 1,
              },
            ],
          },
        }),
      );
      toast.push("Quiz created.", "success");
      props.onCreated();
      props.onClose();
    } catch (error) {
      setErr(error instanceof Error ? error.message : "Failed to create quiz");
    } finally {
      setSaving(false);
    }
  };

  return (
    <GlassDialog open={props.open} title="Create Practice Quiz" onClose={() => props.onClose()}>
      <Show when={err()}>
        {(msg) => (
          <div class="mb-3">
            <ErrorBanner error={msg()} />
          </div>
        )}
      </Show>
      <form onSubmit={submit} class="space-y-3 text-sm">
        <label class="block space-y-1">
          <span class="font-medium text-ink">Title</span>
          <input
            required
            minlength={3}
            value={title()}
            onInput={(e) => setTitle(e.currentTarget.value)}
            class={INPUT_CLS}
          />
        </label>
        <div class="grid gap-3 sm:grid-cols-3">
          <label class="block space-y-1">
            <span class="font-medium text-ink">Subject</span>
            <input required value={subject()} onInput={(e) => setSubject(e.currentTarget.value)} class={INPUT_CLS} />
          </label>
          <label class="block space-y-1">
            <span class="font-medium text-ink">Topic</span>
            <input required value={topic()} onInput={(e) => setTopic(e.currentTarget.value)} class={INPUT_CLS} />
          </label>
          <label class="block space-y-1">
            <span class="font-medium text-ink">Difficulty</span>
            <select
              value={difficulty()}
              onChange={(e) => setDifficulty(e.currentTarget.value as "easy" | "medium" | "hard")}
              class={INPUT_CLS}
            >
              <option value="easy">easy</option>
              <option value="medium">medium</option>
              <option value="hard">hard</option>
            </select>
          </label>
        </div>
        <label class="block space-y-1">
          <span class="font-medium text-ink">Question prompt</span>
          <input required value={prompt()} onInput={(e) => setPrompt(e.currentTarget.value)} class={INPUT_CLS} />
        </label>
        <label class="block space-y-1">
          <span class="font-medium text-ink">Options (one per line, leave blank for short answer)</span>
          <textarea
            rows={4}
            value={optionsText()}
            onInput={(e) => setOptionsText(e.currentTarget.value)}
            class={`${INPUT_CLS} font-mono text-xs`}
          />
        </label>
        <div class="grid gap-3 sm:grid-cols-2">
          <label class="block space-y-1">
            <span class="font-medium text-ink">Correct answer</span>
            <input required value={correct()} onInput={(e) => setCorrect(e.currentTarget.value)} class={INPUT_CLS} />
          </label>
          <label class="block space-y-1">
            <span class="font-medium text-ink">Explanation</span>
            <input value={explanation()} onInput={(e) => setExplanation(e.currentTarget.value)} class={INPUT_CLS} />
          </label>
        </div>
        <div class="flex justify-end gap-2 pt-2">
          <button
            type="button"
            class="rounded-xl border border-edge px-4 py-2 text-xs font-medium text-muted"
            onClick={() => props.onClose()}
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving()}
            class="glass-btn rounded-xl bg-brand px-4 py-2 text-xs font-semibold text-brand-ink disabled:opacity-50"
          >
            {saving() ? "Saving..." : "Save Quiz"}
          </button>
        </div>
      </form>
    </GlassDialog>
  );
}
