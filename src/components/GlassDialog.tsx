import { X } from "@lucide/solid";
import type { JSX } from "@solidjs/web";
import { createEffect, createSignal } from "solid-js";

let nextDialogId = 1;

export function GlassDialog(props: { open: boolean; title: string; onClose: () => void; children: JSX.Element }) {
  const [dialogEl, setDialogEl] = createSignal<HTMLDialogElement>();
  const titleId = `glass-dialog-title-${nextDialogId++}`;

  createEffect(
    () => ({ el: dialogEl(), open: props.open }),
    ({ el, open }) => {
      if (!el) return;
      if (open && !el.open) {
        el.showModal();
      } else if (!open && el.open) {
        el.close();
      }
    },
  );

  // Safari fallback for browsers without declarative <dialog closedby="any">
  createEffect(
    () => dialogEl(),
    (el) => {
      if (!el || "closedBy" in HTMLDialogElement.prototype) return;
      const handleClick = (event: MouseEvent) => {
        if (event.target !== el) return;
        const rect = el.getBoundingClientRect();
        const inside =
          rect.top <= event.clientY &&
          event.clientY <= rect.top + rect.height &&
          rect.left <= event.clientX &&
          event.clientX <= rect.left + rect.width;
        if (!inside) el.close();
      };
      el.addEventListener("click", handleClick);
      return () => el.removeEventListener("click", handleClick);
    },
  );

  return (
    <dialog
      ref={setDialogEl}
      {...({ closedby: "any" } as Record<string, string>)}
      aria-labelledby={titleId}
      class="glass-surface glass-dialog"
      onClose={() => props.onClose()}
    >
      <div class="flex items-center justify-between border-b border-edge px-6 py-4">
        <h2 id={titleId} class="text-lg font-semibold text-ink">
          {props.title}
        </h2>
        <button
          type="button"
          aria-label="Close dialog"
          class="glass-btn rounded-full p-1.5 text-muted hover:bg-surface hover:text-ink"
          onClick={() => dialogEl()?.close()}
        >
          <X class="h-4 w-4" />
        </button>
      </div>
      <div class="p-6">{props.children}</div>
    </dialog>
  );
}
