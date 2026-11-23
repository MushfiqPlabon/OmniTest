import { Search, X } from "@lucide/solid";
import { Show } from "solid-js";

export interface FilterState {
  search: string;
  subject: string;
  difficulty: string;
}

const SUBJECTS = ["math", "science", "reading", "writing", "social_studies"];
const DIFFICULTIES = ["easy", "medium", "hard"];

export function FilterBar(props: {
  value: FilterState;
  onChange: (next: Partial<FilterState>) => void;
  onClear: () => void;
}) {
  const hasFilters = () => Boolean(props.value.search || props.value.subject || props.value.difficulty);

  return (
    <div class="reading-surface flex flex-wrap items-center gap-3 rounded-2xl p-3">
      <div class="relative min-w-[14rem] flex-1">
        <Search class="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-muted" />
        <input
          type="search"
          aria-label="Search by keyword"
          placeholder="Search topic, title, or keyword..."
          value={props.value.search}
          onInput={(e) => props.onChange({ search: e.currentTarget.value })}
          class="w-full rounded-xl border border-edge bg-canvas py-2 pr-3 pl-9 text-sm text-ink placeholder:text-muted"
        />
      </div>

      <select
        aria-label="Filter by subject"
        value={props.value.subject}
        onChange={(e) => props.onChange({ subject: e.currentTarget.value })}
        class="rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink"
      >
        <option value="">All subjects</option>
        {SUBJECTS.map((subj) => (
          <option value={subj}>{subj.replace("_", " ")}</option>
        ))}
      </select>

      <select
        aria-label="Filter by difficulty"
        value={props.value.difficulty}
        onChange={(e) => props.onChange({ difficulty: e.currentTarget.value })}
        class="rounded-xl border border-edge bg-canvas px-3 py-2 text-sm text-ink"
      >
        <option value="">All levels</option>
        {DIFFICULTIES.map((diff) => (
          <option value={diff}>{diff}</option>
        ))}
      </select>

      <Show when={hasFilters()}>
        <button
          type="button"
          class="glass-btn inline-flex items-center gap-1 rounded-xl border border-edge px-3 py-2 text-xs font-medium text-muted hover:text-ink"
          onClick={() => props.onClear()}
        >
          <X class="h-3.5 w-3.5" />
          Reset
        </button>
      </Show>
    </div>
  );
}
