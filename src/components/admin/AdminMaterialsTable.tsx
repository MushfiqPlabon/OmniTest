import { For } from "solid-js";
import type { Schemas } from "@/api/client";
import { MaterialAdminActions } from "@/components/materials/MaterialAdminActions";

export function AdminMaterialsTable(props: {
  items: Schemas["MaterialResponse"][];
  ingestingId: number | null;
  onEdit: (m: Schemas["MaterialResponse"]) => void;
  onReingest: (id: number) => void;
  onDelete: (id: number) => void;
}) {
  return (
    <div class="reading-surface overflow-x-auto rounded-2xl">
      <table class="w-full text-left text-sm">
        <thead class="border-b border-edge text-xs uppercase tracking-wider text-muted">
          <tr>
            <th class="px-4 py-3 font-semibold">Title</th>
            <th class="px-4 py-3 font-semibold">Subject / Topic</th>
            <th class="px-4 py-3 font-semibold">Difficulty</th>
            <th class="px-4 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-edge">
          <For
            each={props.items}
            fallback={
              <tr>
                <td colspan="4" class="px-4 py-6 text-center text-xs text-muted">
                  No study materials found.
                </td>
              </tr>
            }
          >
            {(m) => (
              <tr class="hover:bg-canvas/50">
                <td class="px-4 py-3 font-medium text-ink">{m.title}</td>
                <td class="px-4 py-3 text-xs text-muted">
                  {m.subject} · {m.topic}
                </td>
                <td class="px-4 py-3 text-xs capitalize text-muted">{m.difficulty}</td>
                <td class="px-4 py-3">
                  <div class="flex justify-end">
                    <MaterialAdminActions
                      busy={props.ingestingId === m.id}
                      onEdit={() => props.onEdit(m)}
                      onReingest={() => props.onReingest(m.id)}
                      onDelete={() => props.onDelete(m.id)}
                    />
                  </div>
                </td>
              </tr>
            )}
          </For>
        </tbody>
      </table>
    </div>
  );
}
