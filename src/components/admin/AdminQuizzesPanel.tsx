import { Edit3, Trash2, Users } from "@lucide/solid";
import { createSignal, For } from "solid-js";
import { api, type Schemas, unwrap } from "@/api/client";
import { QuizAttemptsDialog } from "@/components/admin/QuizAttemptsDialog";
import { QuizEditDialog } from "@/components/admin/QuizEditDialog";
import { useToast } from "@/state/toast";

export function AdminQuizzesPanel(props: { items: Schemas["QuizResponse"][]; onChanged: () => void }) {
  const toast = useToast();
  const [editing, setEditing] = createSignal<Schemas["QuizResponse"] | null>(null);
  const [viewing, setViewing] = createSignal<Schemas["QuizResponse"] | null>(null);
  const [attempts, setAttempts] = createSignal<Schemas["AttemptSummaryResponse"][]>([]);
  const [loadingAttempts, setLoadingAttempts] = createSignal(false);

  const openAttempts = async (q: Schemas["QuizResponse"]) => {
    setViewing(q);
    setLoadingAttempts(true);
    try {
      const list = await unwrap(
        api.GET("/api/v1/quizzes/{quiz_id}/attempts", {
          params: { path: { quiz_id: q.id }, query: { limit: 50, offset: 0 } },
        }),
      );
      setAttempts(list);
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Failed to load attempts", "error");
    } finally {
      setLoadingAttempts(false);
    }
  };

  const removeQuiz = async (id: number) => {
    try {
      await unwrap(api.DELETE("/api/v1/quizzes/{quiz_id}", { params: { path: { quiz_id: id } } }));
      toast.push("Quiz deleted", "info");
      props.onChanged();
    } catch (err) {
      toast.push(err instanceof Error ? err.message : "Delete failed", "error");
    }
  };

  return (
    <>
      <div class="reading-surface overflow-x-auto rounded-2xl">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-edge text-xs uppercase tracking-wider text-muted">
            <tr>
              <th class="px-4 py-3 font-semibold">Quiz Title</th>
              <th class="px-4 py-3 font-semibold">Subject / Topic</th>
              <th class="px-4 py-3 font-semibold">Difficulty</th>
              <th class="px-4 py-3 text-right font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-edge">
            <For
              each={props.items}
              fallback={
                <tr>
                  <td colspan="4" class="px-4 py-6 text-center text-xs text-muted">
                    No quizzes created yet.
                  </td>
                </tr>
              }
            >
              {(q) => (
                <tr class="hover:bg-canvas/50">
                  <td class="px-4 py-3 font-medium text-ink">{q.title}</td>
                  <td class="px-4 py-3 text-xs text-muted">
                    {q.subject} · {q.topic}
                  </td>
                  <td class="px-4 py-3 text-xs capitalize text-muted">{q.difficulty}</td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end gap-1">
                      <button
                        type="button"
                        class="rounded-lg p-1.5 text-muted hover:text-brand"
                        aria-label={`Attempts for ${q.title}`}
                        onClick={() => void openAttempts(q)}
                      >
                        <Users class="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        class="rounded-lg p-1.5 text-muted hover:text-ink"
                        aria-label={`Edit ${q.title}`}
                        onClick={() => setEditing(q)}
                      >
                        <Edit3 class="h-3.5 w-3.5" />
                      </button>
                      <button
                        type="button"
                        class="rounded-lg p-1.5 text-muted hover:text-danger"
                        aria-label={`Delete ${q.title}`}
                        onClick={() => void removeQuiz(q.id)}
                      >
                        <Trash2 class="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </For>
          </tbody>
        </table>
      </div>
      <QuizEditDialog quiz={editing()} onClose={() => setEditing(null)} onSaved={() => props.onChanged()} />
      <QuizAttemptsDialog
        quiz={viewing()}
        attempts={attempts()}
        loading={loadingAttempts()}
        onClose={() => setViewing(null)}
      />
    </>
  );
}
