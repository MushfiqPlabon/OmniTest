import autoAnimate from "@formkit/auto-animate";
import { AlertCircle, CheckCircle2, X } from "@lucide/solid";
import { For } from "solid-js";
import { useToast } from "@/state/toast";

export function ToastHost() {
  const toast = useToast();

  return (
    <div
      ref={(el) => autoAnimate(el)}
      class="pointer-events-none fixed right-4 bottom-4 z-50 flex w-full max-w-sm flex-col gap-2"
      aria-live="polite"
    >
      <For each={toast.items()}>
        {(item) => (
          <div
            class={[
              "glass-surface pointer-events-auto flex items-center justify-between gap-3 rounded-2xl px-4 py-3 text-sm shadow-lg",
              item.tone === "error" ? "border-danger/40" : "border-edge",
            ]}
          >
            <div class="flex items-center gap-2.5 text-ink">
              {item.tone === "error" ? (
                <AlertCircle class="h-4 w-4 shrink-0 text-danger" />
              ) : (
                <CheckCircle2 class="h-4 w-4 shrink-0 text-ok" />
              )}
              <span>{item.message}</span>
            </div>
            <button
              type="button"
              aria-label="Dismiss notification"
              class="rounded-full p-1 text-muted hover:text-ink"
              onClick={() => toast.dismiss(item.id)}
            >
              <X class="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </For>
    </div>
  );
}
