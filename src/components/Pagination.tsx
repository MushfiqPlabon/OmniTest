import { ChevronLeft, ChevronRight } from "@lucide/solid";
import { Show } from "solid-js";

export function Pagination(props: {
  page: number;
  pages: number;
  total: number;
  onPageChange: (nextPage: number) => void;
}) {
  return (
    <Show when={props.pages > 1}>
      <div class="flex flex-wrap items-center justify-between gap-3 pt-2 text-xs text-muted">
        <span class="tabular-nums">
          Page {props.page} of {props.pages} ({props.total} total)
        </span>
        <div class="flex items-center gap-2">
          <button
            type="button"
            disabled={props.page <= 1}
            class="glass-btn inline-flex items-center gap-1 rounded-xl border border-edge bg-surface px-3 py-1.5 font-medium text-ink disabled:opacity-45"
            onClick={() => props.onPageChange(props.page - 1)}
          >
            <ChevronLeft class="h-3.5 w-3.5" />
            Previous
          </button>
          <button
            type="button"
            disabled={props.page >= props.pages}
            class="glass-btn inline-flex items-center gap-1 rounded-xl border border-edge bg-surface px-3 py-1.5 font-medium text-ink disabled:opacity-45"
            onClick={() => props.onPageChange(props.page + 1)}
          >
            Next
            <ChevronRight class="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
    </Show>
  );
}
