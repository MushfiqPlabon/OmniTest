import { Show } from "solid-js";
import type { Schemas } from "@/api/client";
import { GlassDialog } from "@/components/GlassDialog";
import { MaterialForm } from "@/components/materials/MaterialForm";

interface MaterialAdminDialogProps {
  open: boolean;
  editing: Schemas["MaterialResponse"] | null;
  onClose: () => void;
  onSaved: () => void;
}

export function MaterialAdminDialog(props: MaterialAdminDialogProps) {
  return (
    <GlassDialog
      open={props.open}
      title={props.editing ? "Edit study material" : "New study material"}
      onClose={() => props.onClose()}
    >
      <Show when={props.open}>
        <MaterialForm editing={props.editing} onClose={() => props.onClose()} onSaved={() => props.onSaved()} />
      </Show>
    </GlassDialog>
  );
}
