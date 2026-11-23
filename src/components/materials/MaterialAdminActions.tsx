import { Edit3, RefreshCw, Trash2 } from "@lucide/solid";

interface MaterialAdminActionsProps {
  busy: boolean;
  onEdit: () => void;
  onReingest: () => void;
  onDelete: () => void;
}

export function MaterialAdminActions(props: MaterialAdminActionsProps) {
  return (
    <div class="flex items-center gap-1">
      <button
        type="button"
        class="rounded-lg p-1.5 text-muted hover:text-ink"
        onClick={() => props.onEdit()}
        aria-label="Edit material"
      >
        <Edit3 class="h-3.5 w-3.5" />
      </button>
      <button
        type="button"
        class="rounded-lg p-1.5 text-muted hover:text-brand disabled:opacity-40"
        disabled={props.busy}
        onClick={() => props.onReingest()}
        aria-label="Re-ingest embeddings"
      >
        <RefreshCw class={props.busy ? "h-3.5 w-3.5 animate-spin" : "h-3.5 w-3.5"} />
      </button>
      <button
        type="button"
        class="rounded-lg p-1.5 text-muted hover:text-danger"
        onClick={() => props.onDelete()}
        aria-label="Delete material"
      >
        <Trash2 class="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
