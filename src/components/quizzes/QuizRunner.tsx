import { createSignal, For, Show } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { QuizResults } from "@/components/quizzes/QuizResults";
import { useToast } from "@/state/toast";

function extractAnswer(raw: string, qType: string): string {
  const clean = raw.trim();
  if (qType === "mcq" && clean.length >= 2 && /[A-Za-z]/.test(clean[0]) && [".", ")", ":"].includes(clean[1])) {
    return clean[0].toUpperCase();
  }
  return clean;
}

export function QuizRunner(props: { quiz: Schemas["QuizWithQuestionsResponse"] }) {
  const toast = useToast();
  const [answers, setAnswers] = createSignal<Record<string, string>>({});
  const [submitting, setSubmitting] = createSignal(false);
  const [result, setResult] = createSignal<Schemas["AttemptResponse"] | null>(null);

  const questions = () => [...(props.quiz.questions ?? [])].sort((a, b) => a.order_num - b.order_num);
  const setAnswer = (qid: number, val: string) => setAnswers((prev) => ({ ...prev, [String(qid)]: val }));

  const handleSubmit = async (e: SubmitEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const normalized: Record<string, string> = {};
      for (const q of questions()) {
        normalized[String(q.id)] = extractAnswer(answers()[String(q.id)] ?? "", q.type);
      }
      const res = await unwrap(
        api.POST("/api/v1/quizzes/{quiz_id}/attempt", {
          params: { path: { quiz_id: props.quiz.id } },
          body: { answers: normalized },
        }),
      );
      setResult(res);
      toast.push(`Score: ${res.score}/${res.max_score} (${res.percentage}%)`, "success");
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Failed to submit quiz", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div class="space-y-5">
      <div class="reading-surface rounded-2xl p-5">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2 border-b border-edge pb-3">
          <div>
            <h2 class="text-lg font-bold text-ink">{props.quiz.title}</h2>
            <p class="text-xs text-muted">
              {props.quiz.subject} · {props.quiz.topic} · {props.quiz.difficulty}
            </p>
          </div>
          <span class="rounded-full bg-canvas px-3 py-1 font-mono text-xs text-ink tabular-nums">
            {questions().length} questions
          </span>
        </div>

        <Show
          when={questions().length > 0}
          fallback={<p class="text-sm text-muted">This quiz has no questions yet.</p>}
        >
          <form onSubmit={handleSubmit} class="space-y-5">
            <For each={questions()}>
              {(q, idx) => (
                <fieldset class="space-y-2.5 border-b border-edge pb-4 last:border-b-0">
                  <legend class="text-sm font-semibold text-ink">
                    {idx() + 1}. {q.prompt}
                  </legend>
                  <Show
                    when={q.type === "mcq" && q.options && q.options.length > 0}
                    fallback={
                      <input
                        type="text"
                        value={answers()[String(q.id)] ?? ""}
                        onInput={(e) => setAnswer(q.id, e.currentTarget.value)}
                        placeholder="Type your answer..."
                        class="w-full rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink"
                      />
                    }
                  >
                    <div class="grid gap-2">
                      <For each={q.options ?? []}>
                        {(opt) => (
                          <label class="flex cursor-pointer items-center gap-2.5 rounded-xl border border-edge bg-canvas px-3.5 py-2 text-sm text-ink hover:border-brand">
                            <input
                              type="radio"
                              name={`quiz-${props.quiz.id}-q-${q.id}`}
                              checked={answers()[String(q.id)] === opt}
                              onChange={() => setAnswer(q.id, opt)}
                            />
                            <span>{opt}</span>
                          </label>
                        )}
                      </For>
                    </div>
                  </Show>
                </fieldset>
              )}
            </For>

            <button
              type="submit"
              disabled={submitting()}
              class="glass-btn rounded-xl bg-brand px-5 py-2.5 text-sm font-semibold text-brand-ink disabled:opacity-50"
            >
              {submitting() ? "Grading..." : "Submit Quiz"}
            </button>
          </form>
        </Show>
      </div>

      <Show when={result()} keyed>
        {(res) => <QuizResults result={res} />}
      </Show>
    </div>
  );
}
