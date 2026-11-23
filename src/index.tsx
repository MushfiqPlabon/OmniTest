import "@/styles/tokens.css";
import "@/styles/glass.css";
import { GraduationCap } from "@lucide/solid";
import { createRouter, defineRoutes } from "@solidjs/router";
import { render } from "@solidjs/web";
import { Errored, Loading, Show } from "solid-js";
import { AppShell } from "@/components/AppShell";
import { ErrorBanner, LoadingSkeleton } from "@/components/States";
import { ThemeToggle } from "@/components/ThemeToggle";
import { ToastHost } from "@/components/ToastHost";
import { AnalyticsPage } from "@/pages/AnalyticsPage";
import { AuthPage } from "@/pages/AuthPage";
import { ChatPage } from "@/pages/ChatPage";
import { EssaysPage } from "@/pages/EssaysPage";
import { MaterialsPage } from "@/pages/MaterialsPage";
import { QuizzesPage } from "@/pages/QuizzesPage";
import { AuthProvider, useAuth } from "@/state/auth";
import { initThemeSync } from "@/state/theme";
import { ToastProvider } from "@/state/toast";

const AppRouter = createRouter({
  routes: defineRoutes([
    { path: "/", component: ChatPage },
    { path: "/chat", component: ChatPage },
    { path: "/quizzes", component: QuizzesPage },
    { path: "/essays", component: EssaysPage },
    { path: "/materials", component: MaterialsPage },
    { path: "/analytics", component: AnalyticsPage },
    { path: "*", component: ChatPage },
  ]),
});

function SignedOutView() {
  return (
    <div class="mx-auto flex min-h-dvh max-w-7xl flex-col px-4 pt-3 pb-10 sm:px-6">
      <header class="glass-surface sticky top-3 z-30 mb-6 flex items-center justify-between gap-3 rounded-2xl px-4 py-2.5">
        <div class="flex items-center gap-2 font-display text-base font-bold text-ink">
          <GraduationCap class="h-5 w-5 text-brand" />
          <span>OmniTest</span>
        </div>
        <ThemeToggle />
      </header>
      <main class="flex-1">
        <AuthPage />
      </main>
    </div>
  );
}

function Workspace() {
  const auth = useAuth();
  return (
    <Errored
      fallback={(err, reset) => (
        <div class="mx-auto max-w-2xl p-6">
          <ErrorBanner error={err} onRetry={reset} />
        </div>
      )}
    >
      <Loading
        fallback={
          <div class="mx-auto max-w-4xl p-6">
            <LoadingSkeleton label="Restoring session..." rows={3} />
          </div>
        }
      >
        <Show when={auth.user()} fallback={<SignedOutView />}>
          <AppRouter>{(p) => <AppShell>{p.children}</AppShell>}</AppRouter>
        </Show>
      </Loading>
    </Errored>
  );
}

function App() {
  initThemeSync();
  return (
    <ToastProvider>
      <AuthProvider>
        <Workspace />
        <ToastHost />
      </AuthProvider>
    </ToastProvider>
  );
}

const root = document.getElementById("root");
if (root) render(() => <App />, root);
