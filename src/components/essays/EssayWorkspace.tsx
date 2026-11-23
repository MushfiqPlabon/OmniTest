import { ArrowLeft, Send } from "@lucide/solid";
import { createSignal, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { EssayFeedback } from "@/components/essays/EssayFeedback";
import { useToast } from "@/state/toast";

interface EssayWorkspaceProps {
  prompt: Schemas["PromptResponse"];
  onBack: () => void;
  onGraded: () => void;
}

export function EssayWorkspace(props: EssayWorkspaceProps) {
  const toast = useToast();
  const [draft, setDraft] = createSignal("");
  const [submitting, setSubmitting] = createSignal(false);
  const [graded, setGraded] = createSignal<Schemas["EssayResponse"] | null>(null);

  const wordCount = () => (draft().trim() ? draft().trim().split(/\s+/).length : 0);

  const submitEssay = async (e: SubmitEvent) => {
    e.preventDefault();
    if (!draft().trim()) return;
    setSubmitting(true);
    try {
      const res = await unwrap(
        api.POST("/api/v1/essays/prompts/{prompt_id}/submit", {
          params: { path: { prompt_id: props.prompt.id } },
          body: { response_text: draft() },
        }),
      );
      setGraded(res);
      props.onGraded();
      toast.push("Essay graded", "success");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Failed to grade essay", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div class="space-y-4">
      <button
        type="button"
        class="glass-btn inline-flex items-center gap-1.5 rounded-xl border border-edge bg-surface px-3 py-1.5 text-xs font-medium text-ink"
        onClick={() => props.onBack()}
      >
        <ArrowLeft class="h-3.5 w-3.5" /> All prompts
      </button>

      <article class="reading-surface rounded-2xl p-5 space-y-2">
        <div class="flex flex-wrap items-center gap-2 text-xs text-muted">
          <span class="rounded-full bg-brand/15 px-2.5 py-0.5 font-medium text-brand">{props.prompt.subject}</span>
          <span>{props.prompt.topic}</span>
          <span>· {props.prompt.difficulty}</span>
          <span class="tabular-nums">· {props.prompt.rubric.max_score} pts max</span>
        </div>
        <p class="text-sm sm:text-base font-medium leading-relaxed text-ink">{props.prompt.prompt_text}</p>
      </article>

      <Show
        when={graded()}
        keyed
        fallback={
          <form class="reading-surface rounded-2xl p-5 space-y-3" onSubmit={submitEssay}>
            <div class="flex items-center justify-between text-xs text-muted">
              <span>Your response</span>
              <span class="tabular-nums">{wordCount()} words</span>
            </div>
            <textarea
              class="w-full min-h-60 rounded-xl border border-edge bg-canvas px-3.5 py-2.5 text-sm leading-relaxed text-ink"
              required
              placeholder="Write a structured response addressing the prompt..."
              value={draft()}
              onInput={(e) => setDraft(e.currentTarget.value)}
            />
            <div class="flex justify-end">
              <button
                type="submit"
                class="glass-btn inline-flex items-center gap-1.5 rounded-xl bg-brand px-4 py-2 text-sm font-semibold text-brand-ink disabled:opacity-50"
                disabled={submitting() || !draft().trim()}
              >
                <Send class="h-4 w-4" />
                {submitting() ? "Grading..." : "Submit for grading"}
              </button>
            </div>
          </form>
        }
      >
        {(g) => (
          <EssayFeedback
            essay={g}
            rubric={props.prompt.rubric}
            onReset={() => {
              setGraded(null);
              setDraft("");
            }}
          />
        )}
      </Show>
    </div>
  );
}
