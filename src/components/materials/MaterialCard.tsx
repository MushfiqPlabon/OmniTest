import { BookOpen } from "@lucide/solid";
import type { JSX } from "@solidjs/web";
import type { Schemas } from "@/api/client";

export function MaterialCard(props: {
  material: Schemas["MaterialResponse"];
  onRead: (m: Schemas["MaterialResponse"]) => void;
  actions?: JSX.Element;
}) {
  return (
    <article class="card-hover reading-surface flex flex-col justify-between gap-4 rounded-2xl p-5">
      <div class="space-y-2">
        <div class="flex items-center justify-between gap-2">
          <span class="rounded-full bg-brand/15 px-2.5 py-0.5 text-xs font-medium text-brand">
            {props.material.subject}
          </span>
          <span class="text-xs capitalize text-muted">{props.material.difficulty}</span>
        </div>
        <h2 class="text-base font-semibold leading-snug text-ink">{props.material.title}</h2>
        <p class="text-xs text-muted">{props.material.topic}</p>
      </div>
      <div class="flex items-center justify-between gap-2 pt-1">
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1.5 rounded-xl bg-brand px-3.5 py-1.5 text-xs font-semibold text-brand-ink"
          onClick={() => props.onRead(props.material)}
        >
          <BookOpen class="h-3.5 w-3.5" /> Read guide
        </button>
        {props.actions}
      </div>
    </article>
  );
}
