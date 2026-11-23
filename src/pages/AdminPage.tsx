import { createMemo, createSignal, Errored, Loading, refresh, Show } from "solid-js";
import { api, unwrap } from "@/api/client";
import { AdminHeader, AdminKpiStrip } from "@/components/admin/AdminBanner";
import { AdminTabs } from "@/components/admin/AdminTabs";
import { EssayAdminDialog } from "@/components/essays/EssayAdminDialog";
import { MaterialAdminDialog } from "@/components/materials/MaterialAdminDialog";
import { QuizAdminDialog } from "@/components/quizzes/QuizAdminDialog";
import { EmptyState, ErrorBanner, LoadingSkeleton } from "@/components/States";
import { useAuth } from "@/state/auth";

export function AdminPage() {
  const auth = useAuth();
  const [matOpen, setMatOpen] = createSignal(false);
  const [quizOpen, setQuizOpen] = createSignal(false);
  const [promptOpen, setPromptOpen] = createSignal(false);

  const dashboard = createMemo(async () => {
    const [health, materials, quizzes, prompts] = await Promise.all([
      unwrap(api.GET("/api/v1/health")),
      unwrap(api.GET("/api/v1/materials", { params: { query: { page: 1, size: 20 } } })),
      unwrap(api.GET("/api/v1/quizzes", { params: { query: { page: 1, size: 20 } } })),
      unwrap(api.GET("/api/v1/essays/prompts", { params: { query: { page: 1, size: 20 } } })),
    ]);
    return { health, materials, quizzes, prompts };
  });

  return (
    <Show
      when={auth.isAdmin()}
      fallback={
        <EmptyState
          title="Admin access required"
          message="Sign in as an administrator to access curriculum management."
        />
      }
    >
      <div class="space-y-6">
        <AdminHeader
          onNewMaterial={() => setMatOpen(true)}
          onNewQuiz={() => setQuizOpen(true)}
          onNewPrompt={() => setPromptOpen(true)}
        />

        <Errored
          fallback={(err, reset) => (
            <ErrorBanner
              error={err}
              onRetry={() => {
                reset();
                void refresh(dashboard);
              }}
            />
          )}
        >
          <Loading fallback={<LoadingSkeleton label="Loading admin console..." rows={4} />}>
            <AdminKpiStrip
              materials={dashboard().materials.total}
              quizzes={dashboard().quizzes.total}
              prompts={dashboard().prompts.total}
              healthText={`${dashboard().health.status} · v${dashboard().health.version}`}
            />
            <AdminTabs
              materials={dashboard().materials.items}
              quizzes={dashboard().quizzes.items}
              prompts={dashboard().prompts.items}
              onRefresh={() => void refresh(dashboard)}
            />
          </Loading>
        </Errored>

        <MaterialAdminDialog
          open={matOpen()}
          editing={null}
          onClose={() => setMatOpen(false)}
          onSaved={() => void refresh(dashboard)}
        />
        <QuizAdminDialog
          open={quizOpen()}
          onClose={() => setQuizOpen(false)}
          onCreated={() => void refresh(dashboard)}
        />
        <EssayAdminDialog
          open={promptOpen()}
          onClose={() => setPromptOpen(false)}
          onCreated={() => void refresh(dashboard)}
        />
      </div>
    </Show>
  );
}
