import { BarChart3, BookOpen, CheckSquare, GraduationCap, LogOut, Menu, MessageSquare, PenTool } from "@lucide/solid";
import { useLocation, useNavigate } from "@solidjs/router";
import type { JSX } from "@solidjs/web";
import { createSignal, For, Show } from "solid-js";
import { GlassDialog } from "@/components/GlassDialog";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useAuth } from "@/state/auth";

const NAV_ITEMS = [
  { path: "/chat", label: "AI Tutor", icon: MessageSquare },
  { path: "/quizzes", label: "Quizzes", icon: CheckSquare },
  { path: "/essays", label: "Essays", icon: PenTool },
  { path: "/materials", label: "Study Library", icon: BookOpen },
  { path: "/analytics", label: "Analytics", icon: BarChart3 },
];

export function AppShell(props: { children: JSX.Element }) {
  const auth = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = createSignal(false);

  const goTo = (href: string) => {
    setDrawerOpen(false);
    const runNav = () => navigate(href);
    const focusHeading = () => document.getElementById("page-heading")?.focus();

    if ("startViewTransition" in document && typeof document.startViewTransition === "function") {
      const vt = document.startViewTransition(() => runNav());
      vt.ready.catch(() => {});
      vt.updateCallbackDone.catch(() => {});
      vt.finished.catch(() => {}).finally(focusHeading);
    } else {
      runNav();
      queueMicrotask(focusHeading);
    }
  };

  const isActive = (path: string) => location.pathname === path || (path === "/chat" && location.pathname === "/");

  const renderLinks = (mobile = false) => (
    <For each={NAV_ITEMS}>
      {(item) => {
        const Icon = item.icon;
        return (
          <a
            href={item.path}
            aria-current={isActive(item.path) ? "page" : undefined}
            onClick={(e) => {
              e.preventDefault();
              goTo(item.path);
            }}
            class={[
              "glass-btn inline-flex items-center gap-2 rounded-xl text-sm font-medium",
              mobile ? "px-3.5 py-2.5" : "px-3 py-1.5",
              isActive(item.path)
                ? "bg-brand text-brand-ink shadow-sm"
                : "text-muted hover:bg-surface/80 hover:text-ink",
            ]}
          >
            <Icon class="h-4 w-4" />
            <span>{item.label}</span>
          </a>
        );
      }}
    </For>
  );

  return (
    <div class="mx-auto flex min-h-dvh max-w-7xl flex-col px-4 pt-3 pb-10 sm:px-6">
      <header class="glass-surface sticky top-3 z-30 mb-6 flex items-center justify-between gap-3 rounded-2xl px-4 py-2.5">
        <div class="flex items-center gap-3">
          <Show when={auth.user()}>
            <button
              type="button"
              aria-label="Open navigation menu"
              class="glass-btn rounded-xl border border-edge p-2 text-ink lg:hidden"
              onClick={() => setDrawerOpen(true)}
            >
              <Menu class="h-4 w-4" />
            </button>
          </Show>
          <a
            href="/chat"
            onClick={(e) => {
              e.preventDefault();
              goTo("/chat");
            }}
            class="flex items-center gap-2 font-display text-base font-bold text-ink"
          >
            <GraduationCap class="h-5 w-5 text-brand" />
            <span>OmniTest</span>
          </a>
        </div>

        <Show when={auth.user()}>
          <nav aria-label="Workspace sections" class="hidden items-center gap-1 lg:flex">
            {renderLinks(false)}
          </nav>
        </Show>

        <div class="flex items-center gap-2">
          <ThemeToggle />
          <Show when={auth.user()} keyed>
            {(u) => (
              <div class="flex items-center gap-2">
                <span class="hidden rounded-full border border-edge bg-surface px-2.5 py-1 text-xs font-medium text-ink sm:inline-flex">
                  {u.full_name} · {u.role.toUpperCase()}
                </span>
                <button
                  type="button"
                  aria-label="Sign out"
                  class="glass-btn inline-flex items-center gap-1 rounded-full border border-edge bg-surface/80 px-2.5 py-1.5 text-xs font-medium text-muted hover:text-danger"
                  onClick={() => auth.logout()}
                >
                  <LogOut class="h-3.5 w-3.5" />
                  <span class="hidden md:inline">Sign out</span>
                </button>
              </div>
            )}
          </Show>
        </div>
      </header>

      <GlassDialog open={drawerOpen()} title="Workspace Navigation" onClose={() => setDrawerOpen(false)}>
        <nav aria-label="Mobile navigation" class="flex flex-col gap-1.5">
          {renderLinks(true)}
        </nav>
      </GlassDialog>

      <main class="flex-1">{props.children}</main>
    </div>
  );
}
