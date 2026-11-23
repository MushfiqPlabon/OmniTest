import { Plus, Trash2 } from "@lucide/solid";
import { For } from "solid-js";
import type { Schemas } from "@/api/client";

const INPUT_CLS = "w-full rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink";

export function EssayRubricFields(props: {
  maxScore: number;
  onMaxScore: (next: number) => void;
  criteria: Schemas["RubricCriterion"][];
  onChangeCriteria: (updater: (prev: Schemas["RubricCriterion"][]) => Schemas["RubricCriterion"][]) => void;
}) {
  const updateAt = (idx: number, patch: Partial<Schemas["RubricCriterion"]>) =>
    props.onChangeCriteria((prev) => prev.map((c, i) => (i === idx ? { ...c, ...patch } : c)));

  return (
    <div class="space-y-2">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <label class="text-xs font-medium text-ink">
          Max score:{" "}
          <input
            type="number"
            min={1}
            max={100}
            class="ml-1 inline-block w-16 rounded-xl border border-edge bg-canvas px-2 py-1 text-center text-xs text-ink tabular-nums"
            value={props.maxScore}
            onInput={(e) => props.onMaxScore(Number(e.currentTarget.value) || 12)}
          />
        </label>
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1 rounded-xl border border-edge bg-surface px-2.5 py-1 text-xs font-medium text-ink"
          onClick={() => props.onChangeCriteria((p) => [...p, { name: "", max: 4, desc: "" }])}
        >
          <Plus class="h-3.5 w-3.5" /> Add criterion
        </button>
      </div>
      <For each={props.criteria}>
        {(c, idx) => (
          <div class="grid grid-cols-[1fr_4rem_1fr_auto] items-center gap-2">
            <input
              class={INPUT_CLS}
              placeholder="Criterion"
              value={c.name}
              onInput={(e) => updateAt(idx(), { name: e.currentTarget.value })}
            />
            <input
              type="number"
              min={1}
              class={`${INPUT_CLS} text-center tabular-nums`}
              value={c.max}
              onInput={(e) => updateAt(idx(), { max: Number(e.currentTarget.value) || 1 })}
            />
            <input
              class={INPUT_CLS}
              placeholder="Description"
              value={c.desc}
              onInput={(e) => updateAt(idx(), { desc: e.currentTarget.value })}
            />
            <button
              type="button"
              class="rounded-lg p-1.5 text-muted hover:text-danger"
              aria-label="Remove criterion"
              onClick={() => props.onChangeCriteria((p) => p.filter((_, i) => i !== idx()))}
            >
              <Trash2 class="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </For>
    </div>
  );
}
