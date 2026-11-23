import { Errored, For, Loading, Show } from "solid-js";
import type { Schemas } from "@/api/client";
import { EssayFeedback } from "@/components/essays/EssayFeedback";
import { EmptyState, ErrorBanner, LoadingSkeleton } from "@/components/States";

export function EssayHistoryList(props: { items: () => Schemas["EssayResponse"][]; onRetry: () => void }) {
  return (
    <Errored
      fallback={(err, reset) => (
        <ErrorBanner
          error={err}
          onRetry={() => {
            reset();
            props.onRetry();
          }}
        />
      )}
    >
      <Loading fallback={<LoadingSkeleton label="Loading submissions..." rows={3} />}>
        <Show
          when={props.items().length > 0}
          fallback={<EmptyState title="No submissions yet" message="Pick a prompt to write your first graded essay." />}
        >
          <div class="space-y-4">
            <For each={props.items()}>{(item) => <EssayFeedback essay={item} />}</For>
          </div>
        </Show>
      </Loading>
    </Errored>
  );
}
