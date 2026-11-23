import { AlertCircle, RefreshCw } from "@lucide/solid";
import type { JSX } from "@solidjs/web";
import { createSignal, onSettled, Show } from "solid-js";

export function LoadingSkeleton(props: { label?: string; rows?: number }) {
  const [slowNotice, setSlowNotice] = createSignal(false);

  onSettled(() => {
    const timer = window.setTimeout(() => setSlowNotice(true), 4000);
    return () => window.clearTimeout(timer);
  });

  const placeholders = () => Array.from({ length: props.rows ?? 3 }, (_, idx) => idx);

  return (
    <div class="space-y-4" role="status" aria-live="polite">
      <div class="flex items-center justify-between text-sm text-muted">
        <span>{props.label ?? "Loading..."}</span>
        <Show when={slowNotice()}>
          <span class="text-xs text-brand">Waking up Render server (cold start can take ~30s)...</span>
        </Show>
      </div>
      <div class="grid gap-3">
        {placeholders().map(() => (
          <div class="reading-surface h-20 animate-pulse rounded-2xl p-4" />
        ))}
      </div>
    </div>
  );
}

export function EmptyState(props: { title: string; message: string; action?: JSX.Element }) {
  return (
    <div class="reading-surface flex flex-col items-center justify-center gap-2 rounded-2xl p-8 text-center">
      <h3 class="text-base font-semibold text-ink">{props.title}</h3>
      <p class="max-w-md text-sm text-muted">{props.message}</p>
      <Show when={props.action}>
        <div class="mt-2">{props.action}</div>
      </Show>
    </div>
  );
}

export function ErrorBanner(props: { error: unknown; onRetry?: () => void }) {
  const message = () => {
    const err = props.error;
    if (err instanceof Error) return err.message;
    return typeof err === "string" ? err : "Something went wrong. Please try again.";
  };

  return (
    <div
      class="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-danger/35 bg-danger/10 p-4 text-sm"
      role="alert"
    >
      <div class="flex items-center gap-2.5 text-ink">
        <AlertCircle class="h-4 w-4 shrink-0 text-danger" />
        <span>{message()}</span>
      </div>
      <Show when={props.onRetry}>
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1.5 rounded-xl border border-edge bg-surface px-3 py-1.5 text-xs font-medium text-ink"
          onClick={() => props.onRetry?.()}
        >
          <RefreshCw class="h-3.5 w-3.5" />
          Retry
        </button>
      </Show>
    </div>
  );
}
