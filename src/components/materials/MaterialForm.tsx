import { Upload } from "@lucide/solid";
import { createSignal, Show } from "solid-js";
import type { Schemas } from "@/api/client";
import { type Diff, saveMaterialSubmission } from "@/components/materials/materialSave";
import { useToast } from "@/state/toast";

const INPUT_CLS = "w-full rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink";

export function MaterialForm(props: {
  editing: Schemas["MaterialResponse"] | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const toast = useToast();
  const [mode, setMode] = createSignal<"text" | "file">("text");
  const [title, setTitle] = createSignal(() => props.editing?.title ?? "");
  const [subject, setSubject] = createSignal(() => props.editing?.subject ?? "");
  const [topic, setTopic] = createSignal(() => props.editing?.topic ?? "");
  const [difficulty, setDifficulty] = createSignal<Diff>(() => (props.editing?.difficulty as Diff) ?? "medium");
  const [source, setSource] = createSignal(() => props.editing?.source ?? "");
  const [content, setContent] = createSignal(() => props.editing?.content ?? "");
  const [file, setFile] = createSignal<File | null>(null);
  const [saving, setSaving] = createSignal(false);

  const submit = async (e: SubmitEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const msg = await saveMaterialSubmission({
        editingId: props.editing?.id ?? null,
        mode: mode(),
        title: title(),
        subject: subject(),
        topic: topic(),
        difficulty: difficulty(),
        source: source(),
        content: content(),
        file: file(),
      });
      toast.push(msg, "success");
      props.onSaved();
      props.onClose();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Failed to save material", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form class="space-y-3 text-sm" onSubmit={submit}>
      <Show when={!props.editing}>
        <div class="inline-flex rounded-xl border border-edge bg-canvas p-1 text-xs">
          {(["text", "file"] as const).map((tab) => (
            <button
              type="button"
              class={[
                "rounded-lg px-3 py-1 transition-colors",
                mode() === tab ? "bg-brand text-brand-ink font-medium" : "text-muted hover:text-ink",
              ]}
              onClick={() => setMode(tab)}
            >
              {tab === "text" ? "Markdown Text" : "Upload File"}
            </button>
          ))}
        </div>
      </Show>

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
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>
      </div>

      <Show
        when={!props.editing && mode() === "file"}
        fallback={
          <>
            <label class="block space-y-1 text-xs font-medium text-ink">
              <span>Source (optional URL or citation)</span>
              <input class={INPUT_CLS} value={source()} onInput={(e) => setSource(e.currentTarget.value)} />
            </label>
            <label class="block space-y-1 text-xs font-medium text-ink">
              <span>Markdown / LaTeX Content</span>
              <textarea
                class={`${INPUT_CLS} min-h-36 font-mono text-xs`}
                required
                value={content()}
                onInput={(e) => setContent(e.currentTarget.value)}
              />
            </label>
          </>
        }
      >
        <label class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-2xl border border-dashed border-edge bg-canvas/60 p-6 text-center text-xs text-muted hover:border-brand">
          <Upload class="h-5 w-5 text-brand" />
          <span>{file()?.name ?? "Choose a PDF, Markdown, or TXT file"}</span>
          <input
            type="file"
            accept=".pdf,.md,.txt"
            class="sr-only"
            onChange={(e) => setFile(e.currentTarget.files?.[0] ?? null)}
          />
        </label>
      </Show>

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
          {saving() ? "Saving..." : "Save material"}
        </button>
      </div>
    </form>
  );
}
